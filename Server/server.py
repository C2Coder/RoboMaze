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
    public_server = "Robo"
    
    use_proxy = False
    proxy = "hotncold.ddns.net"

    dgkops = False  # Dynamicaly Gen Keys On Public Server
    default_level = 0
    default_maze_size = 10
    kick_timeout = 10 * 60  # 10 minutes (600 secs)
    # kick_timeout = 5*60  # 5 minutes  (300 secs)
    # kick_timeout = 1 * 60  # 1 minute (60 secs)
    # kick_timeout = 10 # (10 secs)


colors = [
    "#ffff00",
    "#ccff00",
    "#99ff00",
    "#66ff00",
    "#33ff00",
    "#00ff00",
    "#00ff33",
    "#00ff66",
    "#00ff99",
    "#00ffcc",
    "#00ffff",
    "#00ccff",
    "#0099ff",
    "#0066ff",
    "#0033ff",
    "#0000ff",
    "#3300ff",
    "#6600ff",
    "#9900ff",
    "#cc00ff",
    "#ff00ff",
    "#ff00cc",
    "#ff0099",
    "#ff0066",
    "#ff0033",
    "#ff0000",
    "#ff3300",
    "#ff6600",
    "#EEBB00",
    "#222222",
    "#FFFFFF",
]

chars = [
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "A",
    "B",
    "K",
    "L",
    "M",
]


def rp(pos):  # real pos
    return pos * 2 + 1


class Maze:
    mazes = {}  # maze_id:[maze[][], level, collected keys]
    sizes = {}  # maze_id:size
    players = {}  # maze_id:user_id
    pixels = {}  # maze_id:pixels[x][y]
    keys = {}  # maze_id:keys[[x, y]]
    player_data = {}  # user_id:[x, y, color/team, last time played, num of keys]

    key_color = "K"
    wall_color = "L"
    empty_color = "M"

    def get_id(user_id):
        for key, val_list in Maze.players.items():
            for val in val_list:
                if val == user_id:
                    return key
        return None  # Return None if the value is not found

    def join(user_id, maze_id):
        # remove player if joined before
        tmp_maze_id = Maze.get_id(user_id)
        if not tmp_maze_id is None:
            tmp = Maze.players[tmp_maze_id]
            tmp.pop(tmp.index(user_id))
            Maze.players[tmp_maze_id] = tmp

        # create new user
        Maze.player_data[user_id] = [
            rp(random.randint(0, Maze.sizes[maze_id] - 1)),  # X
            rp(random.randint(0, Maze.sizes[maze_id] - 1)),  # Y
            chars[random.randint(0, 27)],  # color/team
            time.time(),  # last time played
            0,  # num of keys
        ]

        # add player to player list
        if maze_id in list(Maze.players.keys()):
            tmp = list(Maze.players[maze_id])
            tmp.append(user_id)
            Maze.players[maze_id] = tmp
        else:
            Maze.players[maze_id] = [user_id]

        tmp_maze_list = list(Maze.mazes.keys())

        if not maze_id in tmp_maze_list:
            Maze.generate(maze_id, Config.default_level)

    def is_on_key(user_id, maze_id):
        for key in Maze.keys[maze_id]:
            if (
                rp(key[0]) == Maze.player_data[user_id][0]
                and rp(key[1]) == Maze.player_data[user_id][1]
            ):
                key_list = Maze.keys[maze_id]
                key_list.pop(key_list.index(key))
                Maze.mazes[maze_id][2] = Maze.mazes[maze_id][2] + 1
                Maze.player_data[user_id][4] = Maze.player_data[user_id][4] + 1

                if Config.dgkops:
                    Maze.generate_keys(maze_id, Maze.mazes[maze_id][1])

                print(f"level: {Maze.mazes[maze_id][1]}")
                keys_on_lvl = Maze.mazes[maze_id][1] + 2
                keys_to_lvlup = keys_on_lvl * 2

                if maze_id == Config.public_server:
                    keys_to_lvlup = keys_to_lvlup * 2

                if Maze.mazes[maze_id][2] >= keys_to_lvlup:
                    Maze.mazes[maze_id][2] = 0  # set collected keys to 0
                    Maze.mazes[maze_id][1] += 1  # level + 1
                    Maze.generate(maze_id, Maze.mazes[maze_id][1])
                    return True
                elif len(Maze.keys[maze_id]) == 0:
                    Maze.generate(maze_id, Maze.mazes[maze_id][1])
        return False

    def gen_key(maze_id):
        # gen key
        tmp = [
            random.randint(0, Maze.sizes[maze_id] - 1),
            random.randint(0, Maze.sizes[maze_id] - 1),
        ]

        if maze_id in list(Maze.keys.keys()) and tmp in Maze.keys[maze_id]:
            return Maze.gen_key(maze_id)
        return tmp

    def generate_keys(maze_id, level):
        # generate keys
        keys_on_lvl = level + 2

        if maze_id in list(Maze.keys.keys()):
            count = len(Maze.keys[maze_id])
            tmp = Maze.keys[maze_id]
        else:
            count = 0
            tmp = []
        for _ in range(keys_on_lvl - count):
            tmp.append(Maze.gen_key(maze_id))
        Maze.keys[maze_id] = tmp

    def generate(maze_id, level):
        # generate maze
        maze = np.ones((rp(level + 4), rp(level + 4)))
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
                    and nx < level + 4
                    and ny < level + 4
                    and maze[2 * nx + 1, 2 * ny + 1] == 1
                ):
                    maze[2 * nx + 1, 2 * ny + 1] = 0
                    maze[2 * x + 1 + dx, 2 * y + 1 + dy] = 0
                    stack.append((nx, ny))
                    break
            else:
                stack.pop()
        if maze_id in list(Maze.mazes.keys()):
            Maze.mazes[maze_id] = [maze, level, Maze.mazes[maze_id][2]]
        else:
            Maze.mazes[maze_id] = [maze, level, Config.default_level]

        Maze.sizes[maze_id] = level + 4

        Maze.generate_keys(maze_id, level)

    def move_player(user_id, dir):
        data = Maze.player_data[user_id]
        maze_id = Maze.get_id(user_id)
        if dir == "up":
            if not Maze.pixels[maze_id][data[0]][data[1] - 1] == Maze.wall_color:
                data[1] = data[1] - 1
        elif dir == "down":
            if not Maze.pixels[maze_id][data[0]][data[1] + 1] == Maze.wall_color:
                data[1] = data[1] + 1
        elif dir == "left":
            if not Maze.pixels[maze_id][data[0] - 1][data[1]] == Maze.wall_color:
                data[0] = data[0] - 1
        elif dir == "right":
            if not Maze.pixels[maze_id][data[0] + 1][data[1]] == Maze.wall_color:
                data[0] = data[0] + 1
        data[3] = time.time()

        if Maze.is_on_key(user_id, maze_id):
            data[4] = data[4] + 1

        Maze.player_data[user_id] = data

    def render(maze_id):
        Maze.pixels[maze_id] = [  # create empty array
            [Maze.empty_color for i in range(rp(Maze.sizes[maze_id]))]
            for j in range(rp(Maze.sizes[maze_id]))
        ]

        for y in range(rp(Maze.sizes[maze_id])):  # render walls
            for x in range(rp(Maze.sizes[maze_id])):
                if int(Maze.mazes[maze_id][0][x][y]) == 1:
                    Maze.pixels[maze_id][x][y] = Maze.wall_color

        for key in Maze.keys[maze_id]:  # render keys
            Maze.pixels[maze_id][rp(int(key[0]))][rp(int(key[1]))] = Maze.key_color

        for user_id in Maze.players[maze_id]:  # render players
            Maze.pixels[maze_id][Maze.player_data[user_id][0]][
                Maze.player_data[user_id][1]
            ] = Maze.player_data[user_id][2]

    def kick_not_playing():

        cur_time = time.time()
        
        for maze_id in list(Maze.players.keys()):
            for user_id in Maze.players[maze_id]:
                player_data = Maze.player_data[user_id]
                if player_data[3] + Config.kick_timeout < cur_time:
                    print(f"Kicked {user_id}")
                    Maze.players[maze_id].pop(Maze.players[maze_id].index(user_id))


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
    files = ["mazes.save", "sizes.save", "players.save", "keys.save", "playerdata.save"]
    folder = "save/"

    def init():
        if not os.path.exists(Save.folder):
            os.mkdir(Save.folder)

        files = os.listdir(Save.folder)

        for file in Save.files:
            if file in files:
                Save.load(file)
            else:
                Save.save(file)

    def save_all():
        for file in Save.files:
            Save.save(file)

    def save(file):
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


class Server:
    port = 8000

    def getIp():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    if Config.use_proxy:
        local_ip = Config.proxy
    else:
        local_ip = getIp()

    def loop():
        app.static_folder = "static"
        app.run(host="0.0.0.0", port=Server.port, debug=False)

    def background_func():
        while True:
            time.sleep(60)  # 1 min (60 secs)
            Logger.save_logs()
            Save.save_all()

    def edit_script():
        with open("static/script.js", "r") as file:
            lines = file.readlines()

        lines[0] = f"server_ip = '{Server.local_ip}'\n"
        lines[1] = f"port = {Server.port}\n"
        lines[2] = f"ws_port = {WS.port}\n"

        with open("static/script.js", "w") as file:
            file.writelines(lines)

    def handle_cmd(data_in):
        try:
            data = data_in.strip().split()
            # data = ["elks", "paint", "41", "38", "blue"]

            user_id = data[0]
            cmd = data[1]

            if cmd == "join":
                if len(data) == 2:
                    Maze.join(user_id, user_id)
                else:
                    Maze.join(user_id, data[2])

            elif cmd == "move":
                dir = data[2]
                Maze.move_player(user_id, dir)
            else:
                return "wrong cmd"
            Logger.log("".join(data))
            return "pass"
        except KeyboardInterrupt:
            exit()
        except:
            return "failed"


class WS:
    port = 8001

    async def handler(websocket, path):
        try:
            data = await websocket.recv()
            if "get_pixels" in data:
                Maze.kick_not_playing()
                maze_id = data.split()[1]
                if maze_id in list(Maze.mazes.keys()):
                    Maze.render(maze_id)

                    # backup.save()
                    response = "data:"
                    for y in range(rp(Maze.sizes[maze_id])):
                        for x in range(rp(Maze.sizes[maze_id])):
                            response = response + Maze.pixels[maze_id][x][y]
                else:
                    response = "".join(
                        [
                            "a"
                            for i in range(
                                rp(Maze.sizes[maze_id]) * rp(Maze.sizes[maze_id])
                            )
                        ]
                    )
                await websocket.send(response)
                return
            elif "get_size" in data:
                # TODO send size per maze DONE!!
                maze_id = data.split()[1]
                response = f"size:{rp(Maze.sizes[maze_id])}"
                await websocket.send(response)
                return

            Server.handle_cmd(data)
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
def main_page_response():
    with open("static/index.htm") as index_file:
        return index_file.read()


if __name__ == "__main__":
    Save.init()
    Logger.init()
    if not Config.public_server in list(Maze.mazes.keys()):
        Maze.generate(Config.public_server, Config.default_level)  # create public maze
    Maze.players[Config.public_server] = []
    Server.edit_script()

    bg_t = threading.Thread(target=Server.background_func)
    bg_t.start()

    loop = threading.Thread(target=Server.loop)
    loop.start()

    start_server = websockets.serve(WS.handler, "0.0.0.0", WS.port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
