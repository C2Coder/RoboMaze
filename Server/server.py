#!/bin/python3
from flask import Flask, request
from flask_cors import CORS
import socket
import numpy as np
import random
import os
import pickle
import threading
import time
import websockets
import asyncio


class Config:
    use_proxy = False
    proxy_address = "hotncold.ddns.net"

    public_server = "Robo"
    dgkops = True  # Dynamicaly Gen Keys On Public Server

    default_level = 0
    default_world = 0  # prob gonna break stuff if you cahnge it... sooo dont change :)
    kick_timeout = 10 * 60  # 10 minutes (600 secs)
    # kick_timeout = 5*60  # 5 minutes  (300 secs)
    # kick_timeout = 1 * 60  # 1 minute (60 secs)
    # kick_timeout = 10  # (10 secs)


class Colors:
    colors = {
        "a": "#ffff50",  # \
        "b": "#99ff00",  # |
        "c": "#00ff99",  # |
        "d": "#0099ff",  # |
        "e": "#3300ff",  # |  Used for Players
        "f": "#9900ff",  # |
        "g": "#ff00ff",  # |
        "h": "#ff0099",  # |
        "i": "#ff3300",  # |
        "j": "#ff6600",  # /
        "A": "#ff0000",  # \
        "B": "#ffff00",  # |
        "C": "#00ff00",  # |  Used for keys
        "D": "#00ffff",  # |
        "E": "#0000ff",  # /
        "F": "#222222",  # \
        "G": "#440000",  # |
        "H": "#444400",  # |  Used for walls
        "I": "#004400",  # |
        "J": "#004444",  # |
        "K": "#000044",  # /
        "L": "#ffffff",  # \
        "M": "#ffaaaa",  # |
        "N": "#ffffaa",  # |  Used for empty spaces
        "O": "#aaffaa",  # |
        "P": "#aaffff",  # |
        "Q": "#aaaaff",  # /
        "X": "#D0A000",  # Point
    }

    player_colors = (
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
    )

    key_colors = ("A", "B", "C", "D", "E")

    wall_colors = (
        "F",
        "G",
        "H",
        "I",
        "J",
        "K",
    )
    empty_colors = (
        "L",
        "M",
        "N",
        "O",
        "P",
        "Q",
    )
    point_color = "X"


def rp(pos: int | list) -> int | list:  # real pos
    if isinstance(pos, int):
        return pos * 2 + 1
    elif isinstance(pos, list):
        return [(p * 2) + 1 for p in pos]


def rrp(pos: int | list) -> int | list:  # reverse real pos
    if isinstance(pos, int):
        return (pos - 1) / 2
    elif isinstance(pos, list):
        return [(p - 1) / 2 for p in pos]


class Maze:
    mazes = {}  # maze_id:[[maze[][], level, size, collected points]]
    points = {}  # maze_id:[[[x, y]]]
    pixels = {}  # maze_id:[[[[]]]]
    player_data = (
        {}
    )  # user_id:[x, y, direction, maze_id, world, color, team, last time played, num of points]

    def get_maze_id(user_id: str) -> str:
        try:
            return Maze.player_data[user_id][3]
        except KeyError:
            return ""

    def get_world(user_id: str) -> int:
        try:
            return Maze.player_data[user_id][4]
        except KeyError:
            return -1

    def get_world_color(maze_id: str, world: int) -> int:
        return 0  # TODO - future

    def calc_lvlup_point(lvl: int) -> int:
        return (lvl + 2) * 2

    def calc_lvl_size(lvl: int) -> int:
        return lvl + 4

    def create_new_user(user_id: str):
        Maze.player_data[user_id] = [
            1,  # X
            1,  # Y
            0,  # direction
            "",  # maze_id
            0,  # world_id
            Colors.player_colors[
                random.randint(0, len(Colors.player_colors) - 1)
            ],  # color
            user_id,  # team (default team is your user_id)
            0,  # last time played
            0,  # num of points
        ]

    def join(user_id: str, maze_id: str, world: int) -> None:
        # create new user

        if user_id not in list(Maze.player_data.keys()):
            Maze.create_new_user(user_id)

        # create maze if not found
        if maze_id not in list(Maze.mazes.keys()):
            Maze.gen_maze(maze_id, Config.default_level, world)
            Maze.gen_points(maze_id, world)
            Maze.render(maze_id, world)

        # edit the player data
        Maze.player_data[user_id] = [
            rp(random.randint(0, Maze.mazes[maze_id][world][2] - 1)),  # X
            rp(random.randint(0, Maze.mazes[maze_id][world][2] - 1)),  # Y
            0,  # direction
            maze_id,  # maze_id
            world,  # world_id
            Colors.player_colors[
                random.randint(0, len(Colors.player_colors) - 1)
            ],  # color
            user_id,  # team (default team is your user_id)
            time.time(),  # last time played
            Maze.player_data[user_id][8],  # num of points
        ]

    def is_on_point(user_id: str) -> bool:
        print("checking")
        maze_id: str = Maze.player_data[user_id][3]
        world: int = Maze.player_data[user_id][4]
        p_pos = rrp(Maze.player_data[user_id][0:2])

        if p_pos not in Maze.points[maze_id][world]:
            return False

        print(f"user: {user_id} is on point")
        Maze.points[maze_id][world].remove(p_pos)
        Maze.mazes[maze_id][world][3] += 1  # increment collected points on maze
        if Config.dgkops and maze_id == Config.public_server:
            Maze.gen_points(maze_id, world)
        Maze.try_lvlup(maze_id, world)
        return True

    def try_lvlup(maze_id: str, world: int) -> None:
        cur_lvl = Maze.mazes[maze_id][world][1]
        keys_to_lvlup = Maze.calc_lvlup_point(cur_lvl)

        if maze_id == Config.public_server:
            keys_to_lvlup = keys_to_lvlup * 2

        if Maze.mazes[maze_id][world][3] >= keys_to_lvlup:
            Maze.mazes[maze_id][world][3] = 0  # set collected keys to 0
            Maze.mazes[maze_id][world][1] += 1  # level + 1
            Maze.gen_maze(maze_id, Maze.mazes[maze_id][world][1], world)
            Maze.gen_points(maze_id, world)
            Maze.render(maze_id, world)
        elif len(Maze.points[maze_id][world]) == 0:
            Maze.gen_maze(maze_id, Maze.mazes[maze_id][world][1])
            Maze.render(maze_id, world)

    def _gen_point(maze_id: str, world: int) -> list[int]:
        # gen point
        tmp = [
            random.randint(0, Maze.mazes[maze_id][world][2] - 1),
            random.randint(0, Maze.mazes[maze_id][world][2] - 1),
        ]

        if maze_id in list(Maze.points.keys()) and tmp in Maze.points[maze_id][world]:
            return Maze._gen_point(maze_id, world)

        return tmp

    def gen_points(maze_id: str, world: int) -> None:
        # generate keys
        level = Maze.mazes[maze_id][world][1]
        keys_on_lvl = level + 2

        if maze_id in list(Maze.points.keys()):
            count = len(Maze.points[maze_id][world])
            tmp = list(Maze.points[maze_id][world])
        else:
            Maze.points[maze_id] = []
            while len(Maze.points[maze_id]) <= world + 1:
                Maze.points[maze_id].append([])
            count = 0
            tmp = []

        for _ in range(keys_on_lvl - count):
            tmp.append(Maze._gen_point(maze_id, world))

        Maze.points[maze_id][world] = tmp.copy()

    def gen_maze(maze_id: str, level: int, world: int) -> None:
        # generate maze
        size: int = Maze.calc_lvl_size(level)
        maze = np.ones((rp(size), rp(size)))
        x, y = (0, 0)
        stack = [(x, y)]
        while len(stack) > 0:
            x, y = stack[-1]
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (
                    nx >= 0
                    and ny >= 0
                    and nx < size
                    and ny < size
                    and maze[2 * nx + 1, 2 * ny + 1] == 1
                ):
                    maze[2 * nx + 1, 2 * ny + 1] = 0
                    maze[2 * x + 1 + dx, 2 * y + 1 + dy] = 0
                    stack.append((nx, ny))
                    break
            else:
                stack.pop()

        if maze_id in list(Maze.mazes.keys()):
            while len(Maze.mazes[maze_id]) <= world + 1:
                Maze.mazes[maze_id].append([])
            Maze.mazes[maze_id][world] = [maze, level, Maze.mazes[maze_id][world][2], 0]
        else:
            Maze.mazes[maze_id] = [[] for _ in range(world + 1)]
            Maze.mazes[maze_id][world] = [maze, level, Config.default_level, 0]

        Maze.mazes[maze_id][world][2] = size

    def move_player(user_id: str, dir: str) -> None:
        maze_id: str = Maze.get_maze_id(user_id)
        world: int = Maze.get_world(user_id)

        data = Maze.player_data[user_id].copy()

        if world == -1 or maze_id == "":
            return

        rot = data[2]

        if rot == 0:  # up
            if dir == "forward":
                if (
                    not Maze.pixels[maze_id][world][data[0]][data[1] - 1]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][1] -= 1  # Y
            elif dir == "backward":
                if (
                    not Maze.pixels[maze_id][world][data[0]][data[1] + 1]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][1] += 1  # Y
        elif rot == 1:  # right
            if dir == "forward":
                if (
                    not Maze.pixels[maze_id][world][data[0] + 1][data[1]]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][0] += 1  # X
            elif dir == "backward":
                if (
                    not Maze.pixels[maze_id][world][data[0] - 1][data[1]]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][0] -= 1  # X
        elif rot == 2:  # down

            if dir == "forward":
                if (
                    not Maze.pixels[maze_id][world][data[0]][data[1] + 1]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][1] += 1  # Y
            elif dir == "backward":
                if (
                    not Maze.pixels[maze_id][world][data[0]][data[1] - 1]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][1] -= 1  # Y
        elif rot == 3:  # left
            if dir == "forward":
                if (
                    not Maze.pixels[maze_id][world][data[0] - 1][data[1]]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][0] -= 1  # X
            elif dir == "backward":
                if (
                    not Maze.pixels[maze_id][world][data[0] + 1][data[1]]
                    in Colors.wall_colors
                ):
                    Maze.player_data[user_id][0] += 1  # X

        Maze.player_data[user_id][7] = time.time()

        if Maze.is_on_point(user_id):
            Maze.player_data[user_id][8] += 1

    def rotate_player(user_id: str, dir: str) -> None:
        if dir == "left":
            Maze.player_data[user_id][2] -= 1
        elif dir == "right":
            Maze.player_data[user_id][2] += 1

        if Maze.player_data[user_id][2] < 0:
            Maze.player_data[user_id][2] = 3
        elif Maze.player_data[user_id][2] > 3:
            Maze.player_data[user_id][2] = 0

    def render(maze_id: str, world: int) -> None:
        size = Maze.mazes[maze_id][world][2]
        world_color = Maze.get_world_color(maze_id, world)

        Maze.pixels[maze_id] = []

        while len(Maze.pixels[maze_id]) <= world + 1:
            Maze.pixels[maze_id].append([])

        pixels = [  # create empty array
            [Colors.empty_colors[world_color] for _ in range(rp(size))]
            for _ in range(rp(size))
        ]

        for y in range(rp(size)):  # render walls
            for x in range(rp(size)):
                if int(Maze.mazes[maze_id][world][0][x][y]) == 1:
                    pixels[x][y] = Colors.wall_colors[world_color]

        for point in Maze.points[maze_id][world]:  # render keys
            pixels[rp(int(point[0]))][rp(int(point[1]))] = Colors.point_color

        for user_id in list(Maze.player_data.keys()):  # render players
            if (
                maze_id == Maze.player_data[user_id][3]
                and world == Maze.player_data[user_id][4]
            ):
                pixels[Maze.player_data[user_id][0]][Maze.player_data[user_id][1]] = (
                    Maze.player_data[user_id][5]
                )

        Maze.pixels[maze_id][world] = pixels

    def kick_not_playing() -> None:

        cur_time = time.time()

        for user_id in list(Maze.player_data.keys()):
            if not (Maze.player_data[user_id][7] + Config.kick_timeout) < cur_time:
                continue

            if Maze.player_data[user_id][3] == "" or Maze.player_data[user_id][4] == -1:
                continue

            print(f"Kicked {Nicks.get(user_id)} ({user_id})")
            Maze.player_data[user_id][3] = ""
            Maze.player_data[user_id][4] = ""

    def prepare_send(user_id: str, message_id: str) -> str:
        out = []  # _, left, front, right, x, y, dir, team, num_of_points

        maze_id = Maze.get_maze_id(user_id)
        world = Maze.get_world(user_id)
        nick = Nicks.get(user_id)

        if world == -1 or maze_id == "":
            return

        x = Maze.player_data[user_id][0]
        y = Maze.player_data[user_id][1]
        dir = Maze.player_data[user_id][2]
        team = Maze.player_data[user_id][6]
        num_of_points = Maze.player_data[user_id][8]

        if x > 0:
            p_left = int(Maze.mazes[maze_id][world][0][x - 1][y])
        else:
            p_left = 1  # wall

        if x < Maze.mazes[maze_id][world][2]:
            p_right = int(Maze.mazes[maze_id][world][0][x + 1][y])
        else:
            p_right = 1  # wall

        if y > 0:
            p_up = int(Maze.mazes[maze_id][world][0][x][y - 1])
        else:
            p_up = 1  # wall

        if y < Maze.mazes[maze_id][world][2]:
            p_down = int(Maze.mazes[maze_id][world][0][x][y + 1])
        else:
            p_down = 1  # wall

        out.append("_r_")  # random string so i can handle it differently
        out.append(nick)
        out.append(message_id)

        if dir == 0:  # facing up
            out.append(str(p_left))
            out.append(str(p_up))
            out.append(str(p_right))
        elif dir == 1:  # facing right
            out.append(str(p_up))
            out.append(str(p_right))
            out.append(str(p_down))
        elif dir == 2:  # facing down
            out.append(str(p_right))
            out.append(str(p_down))
            out.append(str(p_left))
        elif dir == 3:  # facing left
            out.append(str(p_down))
            out.append(str(p_left))
            out.append(str(p_up))

        out.append(str(x))
        out.append(str(y))
        out.append(str(dir))
        out.append(str(team))
        out.append(str(num_of_points))

        return " ".join(out)


class Logger:
    logs = []
    file = "logs/logs.txt"
    use = True

    def init():
        if not Logger.use:
            return
        if not os.path.isfile(Logger.file):
            with open(Logger.file, "w") as f:
                f.write("")

    def log(msg):
        if not Logger.use:
            return
        Logger.logs.append(msg)

    def save_logs():
        if not Logger.use:
            return
        with open(Logger.file, "a") as f:
            for log in Logger.logs:
                f.write(f"{log}\n")
            Logger.logs = []


class Save:
    # TODO - rewrite
    files = ["mazes.save", "sizes.save", "players.save", "keys.save", "playerdata.save"]
    folder = "save/"

    def init():
        # TODO - rewrite
        return
        if not os.path.exists(Save.folder):
            os.mkdir(Save.folder)

        files = os.listdir(Save.folder)

        for file in Save.files:
            if file in files:
                Save.load(file)
            else:
                Save.save(file)

    def save_all():
        # TODO - rewrite
        return
        for file in Save.files:
            Save.save(file)

    def save(file):
        # TODO - rewrite
        return
        if file == "mazes.save":
            with open(Save.folder + file, "wb") as f:
                pickle.dump(Maze.mazes, f)
        elif file == "sizes.save":
            with open(Save.folder + file, "wb") as f:
                pickle.dump(Maze.sizes, f)
        elif file == "players.save":
            with open(Save.folder + file, "wb") as f:
                pickle.dump(Maze.players, f)
        elif file == "playerdata.save":
            with open(Save.folder + file, "wb") as f:
                pickle.dump(Maze.player_data, f)
        elif file == "keys.save":
            with open(Save.folder + file, "wb") as f:
                pickle.dump(Maze.keys, f)

    def load(file):
        # TODO - rewrite
        return
        if file == "mazes.save":
            with open(Save.folder + file, "rb") as f:
                Maze.mazes = pickle.load(f)
        elif file == "sizes.save":
            with open(Save.folder + file, "rb") as f:
                Maze.sizes = pickle.load(f)
        elif file == "players.save":
            with open(Save.folder + file, "rb") as f:
                Maze.players = pickle.load(f)
        elif file == "playerdata.save":
            with open(Save.folder + file, "rb") as f:
                Maze.player_data = pickle.load(f)
        elif file == "keys.save":
            with open(Save.folder + file, "rb") as f:
                Maze.keys = pickle.load(f)


class Nicks:
    nicks = {}

    def get(user_id: str) -> str:
        if user_id in list(Nicks.nicks.keys()):
            return Nicks.nicks[user_id]
        return user_id

    def get_user(nick: str) -> str:
        for key, val in list(Nicks.nicks.items()):
            if val == nick:
                return key

    def set(user_id: str, nick: str) -> None:
        Nicks.nicks[user_id] = nick


class Server:
    port = 8000
    proxy_port = 8080

    def getIp() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return str(s.getsockname()[0])

    if Config.use_proxy:
        local_ip = Config.proxy_address
    else:
        local_ip = getIp()

    def loop() -> None:
        app.static_folder = "static"
        app.run(host="0.0.0.0", port=Server.port, debug=False)

    def background_func() -> None:
        while True:
            time.sleep(60)  # 1 min (60 secs)
            Maze.kick_not_playing()
            Logger.save_logs()
            Save.save_all()

    def edit_script() -> None:
        with open("static/script.js", "r") as file:
            lines = file.readlines()

        lines[0] = f"server_ip = '{Server.local_ip}';\n"
        lines[1] = f"http_port = {Server.port};\n"
        lines[2] = f"ws_port = {WS.port};\n"

        lines[3] = f"proxy_server_ip = '{Config.proxy_address}';\n"
        lines[4] = f"proxy_http_port = {Server.proxy_port};\n"
        lines[5] = f"proxy_ws_port = {WS.proxy_port};\n"

        lines[6] = f"update_interval = {1000};\n"

        with open("static/script.js", "w") as file:
            file.writelines(lines)

    def handle_cmd(data_in) -> str:
        try:
            data = data_in.strip().split()
            # data = ["serial", "c2c", "move", "forward"]
            user_id = data[0]
            nick = data[1]
            cmd = data[2]
            message_id = data[-1]

            Nicks.set(user_id, nick)

            if cmd == "join":
                if len(data) == 4:
                    Maze.join(user_id, user_id, Config.default_world)
                else:
                    Maze.join(user_id, data[3], Config.default_world)

            elif cmd == "move":
                dir = data[3]
                Maze.move_player(user_id, dir)

            elif cmd == "rotate":
                dir = data[3]
                Maze.rotate_player(user_id, dir)

            Logger.log(" ".join(data))

            return Maze.prepare_send(user_id, message_id)

        except KeyboardInterrupt:
            exit()


class WS:
    port = 8001
    proxy_port = port

    async def handler(websocket, path) -> None:
        while True:
            try:
                data = await websocket.recv()
                toks = data.split(" ")

                if toks[0] == "get_pixels":
                    if toks[1] in list(Maze.player_data.keys()):
                        user_id = toks[1]
                    elif toks[1] in list(Nicks.nicks.values()):
                        user_id = Nicks.get_user(toks[1])
                    else:
                        response = "error;wrong_nick"
                        await websocket.send(response)
                        continue

                    maze_id = Maze.get_maze_id(user_id)
                    world = Maze.get_world(user_id)
                    pixel_msg = ""
                    size_msg = ""

                    if maze_id in list(Maze.mazes.keys()):
                        Maze.render(maze_id, world)
                        pixels = Maze.pixels[maze_id][world]
                        for y in range(rp(Maze.mazes[maze_id][world][2])):
                            for x in range(rp(Maze.mazes[maze_id][world][2])):
                                pixel_msg += pixels[x][y]

                        size_msg += str(rp(Maze.mazes[maze_id][world][2]))
                        response = f"data;{pixel_msg};{size_msg}"
                    else:
                        response = "error;wrong_user_id"

                    await websocket.send(response)
                elif toks[0] == "ping":
                    await websocket.send("pong")

                else:
                    response = Server.handle_cmd(data)
                    if response != "":
                        await websocket.send(response)

            except KeyboardInterrupt:
                exit()
            # dont care about exceptions
            except websockets.exceptions.ConnectionClosedOK:
                return
            except websockets.exceptions.ConnectionClosedError:
                return
            except websockets.exceptions.ConnectionClosed:
                return


app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def main_page_response() -> str:
    with open("static/index.htm") as index_file:
        return index_file.read()


if __name__ == "__main__":
    # Save.init() # TODO - rewrite
    Logger.init()
    if not Config.public_server in list(Maze.mazes.keys()):
        Maze.gen_maze(Config.public_server, Config.default_level, Config.default_world)
        Maze.gen_points(Config.public_server, Config.default_world)
        Maze.render(Config.public_server, Config.default_world)

    Server.edit_script()

    bg_t = threading.Thread(target=Server.background_func)
    bg_t.start()

    loop = threading.Thread(target=Server.loop)
    loop.start()

    start_server = websockets.serve(WS.handler, "0.0.0.0", WS.port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
