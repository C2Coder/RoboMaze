#!/bin/python3
from flask import Flask, request
from flask_cors import CORS
import socket
import numpy as np
import random
import os
import threading
import time
import websockets
import asyncio
from datetime import datetime


class Config:
    use_proxy = False
    proxy_address = "hotncold.ddns.net"

    public_server = "Robo"
    dgkops = True  # Dynamicaly Gen Keys On Public Server

    default_level = 0
    default_world = 0  # prob gonna break stuff if you change it... sooo don't :)
    kick_timeout = 10 * 60  # 10 minutes (600 secs)
    # kick_timeout = 5*60  # 5 minutes  (300 secs)
    # kick_timeout = 1 * 60  # 1 minute (60 secs)
    # kick_timeout = 10  # (10 secs)


class Colors:

    default_color = "#FF0000"

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb_color):
        return "#{:02x}{:02x}{:02x}".format(*rgb_color)

    def lighten_color(hex_color, factor=0.2):
        rgb_color = Colors.hex_to_rgb(hex_color)
        new_rgb = tuple(int(min(255, c + 255 * factor)) for c in rgb_color)
        return Colors.rgb_to_hex(new_rgb)

    def darken_color(hex_color, factor=0.2):
        rgb_color = Colors.hex_to_rgb(hex_color)
        new_rgb = tuple(int(max(0, c - 255 * factor)) for c in rgb_color)
        return Colors.rgb_to_hex(new_rgb)

    def calc_empty(world_color):  # TODO - REWRITE
        return Colors.lighten_color(world_color, factor=0.9)

    def calc_wall(world_color):  # TODO - REWRITE
        return Colors.darken_color(world_color, factor=0.8)

    def rand_player_color():  # TODO - REWRITE
        return "#FF00FF"

    def calc_point(point_value):
        return "#D0A000"

    # colors = {
    #    "a": "#ffff50",  # \
    #    "b": "#99ff00",  # |
    #    "c": "#00ff99",  # |
    #    "d": "#0099ff",  # |
    #    "e": "#3300ff",  # |  Used for Players
    #    "f": "#9900ff",  # |
    #    "g": "#ff00ff",  # |
    #    "h": "#ff0099",  # |
    #    "i": "#ff3300",  # |
    #    "j": "#ff6600",  # /
    #    "A": "#ff0000",  # \
    #    "B": "#ffff00",  # |
    #    "C": "#00ff00",  # |  Used for keys
    #    "D": "#00ffff",  # |
    #    "E": "#0000ff",  # /
    #    "F": "#222222",  # \
    #    "G": "#440000",  # |
    #    "H": "#444400",  # |  Used for walls
    #    "I": "#004400",  # |
    #    "J": "#004444",  # |
    #    "K": "#000044",  # /
    #    "L": "#ffffff",  # \
    #    "M": "#ffaaaa",  # |
    #    "N": "#ffffaa",  # |  Used for empty spaces
    #    "O": "#aaffaa",  # |
    #    "P": "#aaffff",  # |
    #    "Q": "#aaaaff",  # /
    #    "X": "#D0A000",  # Point
    # }
    #
    # player_colors = (
    #    "a",
    #    "b",
    #    "c",
    #    "d",
    #    "e",
    #    "f",
    #    "g",
    #    "h",
    #    "i",
    # )
    #
    # key_colors = ("A", "B", "C", "D", "E")
    #
    # wall_colors = (
    #    "F",
    #    "G",
    #    "H",
    #    "I",
    #    "J",
    #    "K",
    # )
    # empty_colors = (
    #    "L",
    #    "M",
    #    "N",
    #    "O",
    #    "P",
    #    "Q",
    # )
    # point_color = "X"


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
    # maze_id:[[maze[][], level, size, collected points, maze_color (hex)]]
    mazes = {}
    points = {}  # maze_id:[world:[[x, y, value]]]
    keys = {}  # maze_id: [world:[[x, y, world to tp, x to tp, y to tp]]]
    pixels = {}  # maze_id:[[[[]]]]
    player_data = (
        {}
    )  # user_id:[x, y, direction, maze_id, world, color, team, last time played, num of points]

    def get_maze_id(user_id: str) -> str:
        try:
            return Maze.player_data[user_id][3]
        except KeyError:
            return ""

    def get_world_users(maze_id: str, world: int) -> list[str]:
        tmp = []

        for user_id in list(Maze.player_data.keys()):
            if (
                Maze.player_data[user_id][3] == maze_id
                and Maze.player_data[user_id][4] == world
            ):
                tmp.append(user_id)
        return tmp

    def get_world(user_id: str) -> int:
        try:
            return Maze.player_data[user_id][4]
        except KeyError:
            return -1

    def get_world_color(maze_id: str, world: int) -> int:
        return f"{Maze.mazes[maze_id][world][4]}"

    def calc_lvlup_point(lvl: int) -> int:
        return (lvl + 2) * 2

    def calc_lvl_size(lvl: int) -> int:
        return lvl + 6

    def calc_point_count(lvl: int) -> int:
        return lvl + 2

    def calc_point_value(maze_id: str, world: int, lvl: int, count: int) -> int:
        return 1  # TODO

    def create_new_user(user_id: str):
        Maze.player_data[user_id] = [
            1,  # X
            1,  # Y
            0,  # direction
            "",  # maze_id
            0,  # world_id
            Colors.rand_player_color(),  # color
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
            Colors.rand_player_color(),  # color
            user_id,  # team (default team is your user_id)
            time.time(),  # last time played
            Maze.player_data[user_id][8],  # num of points
        ]

    def move_player(user_id: str, dir: str) -> None:
        maze_id: str = Maze.get_maze_id(user_id)
        world: int = Maze.get_world(user_id)

        data = Maze.player_data[user_id].copy()

        if world == -1 or maze_id == "":
            return

        rot = data[2]

        if rot == 0:  # up
            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] - 1] == "w":
                    Maze.player_data[user_id][1] -= 1  # Y
            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] + 1] == "w":
                    Maze.player_data[user_id][1] += 1  # Y
        elif rot == 1:  # right
            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0] + 1][data[1]] == "w":
                    Maze.player_data[user_id][0] += 1  # X
            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0] - 1][data[1]] == "w":
                    Maze.player_data[user_id][0] -= 1  # X
        elif rot == 2:  # down

            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] + 1] == "w":
                    Maze.player_data[user_id][1] += 1  # Y
            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] - 1] == "w":
                    Maze.player_data[user_id][1] -= 1  # Y
        elif rot == 3:  # left
            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0] - 1][data[1]] == "w":
                    Maze.player_data[user_id][0] -= 1  # X
            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0] + 1][data[1]] == "w":
                    Maze.player_data[user_id][0] += 1  # X

    def rotate_player(user_id: str, dir: str) -> None:
        if dir == "left":
            Maze.player_data[user_id][2] -= 1
        elif dir == "right":
            Maze.player_data[user_id][2] += 1

        if Maze.player_data[user_id][2] < 0:
            Maze.player_data[user_id][2] = 3
        elif Maze.player_data[user_id][2] > 3:
            Maze.player_data[user_id][2] = 0

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

    def is_on_point(user_id: str) -> bool:
        maze_id: str = Maze.player_data[user_id][3]
        world: int = Maze.player_data[user_id][4]
        p_pos = rrp(Maze.player_data[user_id][0:2])

        for i, p in enumerate(Maze.points[maze_id][world]):
            if p[:2] == p_pos:
                print(f"user: {user_id} is on point")
                Maze.points[maze_id][world].pop(i)
                Maze.mazes[maze_id][world][3] += p[2]
                if Config.dgkops and maze_id == Config.public_server:
                    Maze.gen_points(maze_id, world, removed_point=p_pos)
                Maze.try_lvlup(maze_id, world)
                return True
        return False

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

    def _gen_point(
        maze_id: str,
        world: int,
        level: int,
        count: int,
        removed_point: None | list = None,
    ) -> list[int]:
        # gen point
        tmp = [
            random.randint(0, Maze.mazes[maze_id][world][2] - 1),
            random.randint(0, Maze.mazes[maze_id][world][2] - 1),
            Maze.calc_point_value(maze_id, world, level, count),
        ]

        if (
            tmp in Maze.points[maze_id][world]
            or removed_point in Maze.points[maze_id][world]
        ):
            # new iteration
            return Maze._gen_point(maze_id, world, level, count, removed_point)

        return tmp

    def gen_points(maze_id: str, world: int, removed_point: None | list = None) -> None:
        # generate keys
        level = Maze.mazes[maze_id][world][1]
        points_on_lvl = Maze.calc_point_count(level)

        if maze_id in list(Maze.points.keys()):
            count = len(Maze.points[maze_id][world])
            tmp = list(Maze.points[maze_id][world])
        else:
            Maze.points[maze_id] = []
            while len(Maze.points[maze_id]) <= world + 1:
                Maze.points[maze_id].append([])
            count = 0
            tmp = []

        for _ in range(points_on_lvl - count):
            tmp.append(Maze._gen_point(maze_id, world, level, len(tmp), removed_point))

        Maze.points[maze_id][world] = tmp.copy()

    def gen_maze(maze_id: str, level: int, world: int) -> None:
        # generate maze
        size: int = Maze.calc_lvl_size(level)
        _maze = np.ones((rp(size), rp(size)))
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
                    and _maze[2 * nx + 1, 2 * ny + 1] == 1
                ):
                    _maze[2 * nx + 1, 2 * ny + 1] = 0
                    _maze[2 * x + 1 + dx, 2 * y + 1 + dy] = 0
                    stack.append((nx, ny))
                    break
            else:
                stack.pop()
        maze = [[int(n) for n in inner_list] for inner_list in _maze]

        if maze_id in list(Maze.mazes.keys()):
            while len(Maze.mazes[maze_id]) <= world + 1:
                Maze.mazes[maze_id].append([])
            Maze.mazes[maze_id][world] = [
                maze,
                level,
                size,
                Maze.mazes[maze_id][world][3],
                Maze.mazes[maze_id][world][4],
            ]
        else:
            Maze.mazes[maze_id] = [[] for _ in range(world + 1)]
            Maze.mazes[maze_id][world] = [maze, level, size, 0, Colors.default_color]

    def render(maze_id: str, world: int) -> None:
        size = Maze.mazes[maze_id][world][2]
        world_color = Maze.get_world_color(maze_id, world)

        Maze.pixels[maze_id] = []

        # create empty worlds if needed
        while len(Maze.pixels[maze_id]) <= world + 1:
            Maze.pixels[maze_id].append([])

        pixels = [  # create empty array
            ["e" for _ in range(rp(size))] for _ in range(rp(size))
        ]

        for y in range(rp(size)):  # render walls
            for x in range(rp(size)):
                if int(Maze.mazes[maze_id][world][0][x][y]) == 1:
                    pixels[x][y] = "w"

        # NOT USED
        # for point in Maze.points[maze_id][world]:  # render keys
        #     pixels[rp(int(point[0]))][rp(int(point[1]))] = Colors.point_color

        # NOT USED
        # for user_id in list(Maze.player_data.keys()):  # render players
        #     if (
        #         maze_id == Maze.player_data[user_id][3]
        #         and world == Maze.player_data[user_id][4]
        #     ):
        #         pixels[Maze.player_data[user_id][0]][Maze.player_data[user_id][1]] = (
        #             Maze.player_data[user_id][5]
        #         )

        Maze.pixels[maze_id][world] = pixels

    def prepare_send(user_id: str, message_id: str, is_on_point: bool) -> str:
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

        out.append("1" if is_on_point else "0")
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
    folder = "save/"
    backup_folder = "backups/"

    extension = ".save"
    files = ["mazes", "players"]

    backup_interval = 15 * 60  # 15 minutes
    last_backup = 0

    def init():
        files = os.listdir("save")
        for file in Save.files:
            if not file.replace(Save.extension, "") in files:
                with open(f"{Save.folder}{file}{Save.extension}", "w+") as f:
                    f.write("")

    def create_backup():
        Save.last_backup = time.time()

        for file in os.listdir("save"):
            if not file.replace(Save.extension, "") in Save.files:
                os.system(f"rm {Save.folder}{file}")

        for file in Save.files:
            if not os.path.exists(f"{Save.folder}{file}{Save.extension}"):
                continue
            cur_time = datetime.now().strftime("%d.%m.%y-%H:%M:%S-")
            os.system(
                f"cp {Save.folder}{file}{Save.extension} {Save.backup_folder}{cur_time}{file}{Save.extension}"
            )

    def save_all():
        for file in Save.files:
            if not os.path.exists(f"{Save.folder}{file}{Save.extension}"):
                continue
            cur_time = datetime.now().strftime("%d.%m.%y-%H:%M:%S-")
            os.rename(
                f"{Save.folder}{file}{Save.extension}",
                f"{Save.folder}{cur_time}{file}{Save.extension}",
            )

        Save.save_mazes()
        Save.save_players()

    def save_mazes():
        tmp = []
        for maze_id in list(Maze.mazes.keys()):
            tmp.append(f"{maze_id}:")
            for world, data in enumerate(Maze.mazes[maze_id]):
                if data == []:
                    continue
                tmp.append(f"{' '*2}world-{world}:")
                tmp.append(f"{' '*4}maze:")
                for row in data[0]:
                    _tmp = ""
                    for c in row:
                        _tmp += "#" if int(c) else " "
                    tmp.append(f"{' '*6}{_tmp}")

                tmp.append(f"{' '*4}points pos:")
                _tmp = ""
                if maze_id in list(Maze.points.keys()):
                    for p in Maze.points[maze_id][world]:
                        _tmp += f"({p[0]}, {p[1]});"
                tmp.append(f"{' '*6}{_tmp.rstrip(';')}")

                tmp.append(f"{' '*4}lvl:")
                tmp.append(f"{' '*6}{data[1]}")

                tmp.append(f"{' '*4}size:")
                tmp.append(f"{' '*6}{data[2]}")

                tmp.append(f"{' '*4}collected points:")
                tmp.append(f"{' '*6}{data[3]}")

        with open(f"{Save.folder}mazes.save", "x") as f:
            for line in tmp:
                f.write(line + "\n")

    def save_players():
        tmp = []
        for user_id in list(Maze.player_data.keys()):
            tmp.append(f"{user_id}:")
            data = Maze.player_data[user_id]
            tmp.append(f"{' '*2}nick:")
            tmp.append(f"{' '*4}{Nicks.get(user_id)}")
            tmp.append(f"{' '*2}x:")
            tmp.append(f"{' '*4}{data[0]}")
            tmp.append(f"{' '*2}y:")
            tmp.append(f"{' '*4}{data[1]}")
            tmp.append(f"{' '*2}rot:")
            tmp.append(f"{' '*4}{data[2]}")
            tmp.append(f"{' '*2}maze:")
            tmp.append(f"{' '*4}{data[3]}")
            tmp.append(f"{' '*2}world:")
            tmp.append(f"{' '*4}{data[4]}")
            tmp.append(f"{' '*2}color:")
            tmp.append(f"{' '*4}{data[5]}")
            tmp.append(f"{' '*2}team:")
            tmp.append(f"{' '*4}{data[6]}")
            tmp.append(f"{' '*2}collected_points:")
            tmp.append(f"{' '*4}{data[8]}")

        with open(f"{Save.folder}players.save", "x") as f:
            for line in tmp:
                f.write(line + "\n")

    def load_all():
        for file in Save.files:
            if not os.path.exists(f"{Save.folder}{file}{Save.extension}"):
                return
        Save.load_mazes()
        Save.load_players()

    def load_mazes():
        with open(f"{Save.folder}mazes.save", "r") as f:
            lines = [line.replace("\n", "") for line in f.readlines()]

        i = 0
        worlds = {}
        maze_id = ""
        world = 0
        while i < len(lines) - 1:
            if lines[i].count(" ") == 0:
                maze_id = lines[i].rstrip(":")
                worlds[maze_id] = []

            elif "world-" in lines[i]:
                world = int(lines[i].replace("world-", "").replace(":", ""))
                while len(worlds[maze_id]) <= world:
                    worlds[maze_id].append([])

                tmp_maze = []
                o = int(i + 2)
                while o < len(lines) - 1:
                    if "points pos:" in lines[o]:
                        break
                    tmp_maze.append(
                        lines[o].strip().replace("#", "1").replace(" ", "0")
                    )
                    o += 1

                worlds[maze_id][world].append(
                    [[int(n) for n in inner_list] for inner_list in tmp_maze]
                )
                i = int(o - 1)
            elif "points pos:" in lines[i]:
                i += 1
                if not maze_id in list(Maze.points.keys()):
                    Maze.points[maze_id] = []

                while len(Maze.points[maze_id]) <= world:
                    Maze.points[maze_id].append([])

                Maze.points[maze_id][world] = []

                for p in (
                    lines[i]
                    .replace(" ", "")
                    .replace(")", "")
                    .replace("(", "")
                    .split(";")
                ):
                    Maze.points[maze_id][world].append([int(n) for n in p.split(",")])
            elif "lvl:" in lines[i]:
                i += 1
                worlds[maze_id][world].append(int(lines[i].replace(" ", "")))
            elif "size:" in lines[i]:
                i += 1
                worlds[maze_id][world].append(int(lines[i].replace(" ", "")))
            elif "collected points:" in lines[i]:
                i += 1
                worlds[maze_id][world].append(int(lines[i].replace(" ", "")))
            i += 1

        for maze_id in list(worlds.keys()):
            Maze.mazes[maze_id] = []

            for world, world_data in enumerate(worlds[maze_id]):
                if world_data == []:
                    Maze.mazes[maze_id].append(world_data)
                    continue

                if not (
                    len(world_data[0]) == rp(world_data[2])
                    or len(world_data[0][0]) == rp(world_data[2])
                ):
                    print(f"Wrong size in maze:{maze_id} in world:{world}")
                    continue
                elif not Maze.calc_lvl_size(int(world_data[1])) == int(world_data[2]):
                    print(f"Wrong lvl in maze:{maze_id} in world:{world}")
                    continue
                Maze.mazes[maze_id].append(world_data)

    def load_players():
        with open(f"{Save.folder}players.save", "r") as f:
            lines = [line.replace("\n", "") for line in f.readlines()]

        i = 0
        users = {}
        user_id = ""
        while i < len(lines) - 1:
            if lines[i].count("  ") == 0:
                user_id = lines[i].rstrip(":")
                users[user_id] = []

            elif "nick:" in lines[i]:
                i += 1
                users[user_id].append(lines[i].replace("  ", ""))
                for _ in range(8):
                    i += 2
                    users[user_id].append(lines[i].replace("  ", ""))
            i += 1
        for user_id in list(users.keys()):
            Maze.player_data[user_id] = [0 for _ in range(9)]
            Nicks.set(user_id, users[user_id][0])
            for i, o in enumerate([0, 1, 2, 3, 4, 5, 6, 8]):
                Maze.player_data[user_id][o] = users[user_id][i + 1]

            Maze.player_data[user_id][7] = (
                time.time() + 30 * 60  # 30 minutes = 1800 secs
            )  # just so they don't get kicked immediately


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

            if Save.backup_interval + Save.last_backup < time.time():
                Save.create_backup()
            else:
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
            print(data)
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

            Maze.player_data[user_id][7] = time.time()
            is_on_point = Maze.is_on_point(user_id)
            if is_on_point:
                Maze.player_data[user_id][8] += 1

            return Maze.prepare_send(user_id, message_id, is_on_point)

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

                if toks[0] == "ping":
                    await websocket.send("pong")
                    continue
                if toks[0] == "get_pixels":
                    if toks[1] in list(Maze.player_data.keys()):
                        user_id = toks[1]
                    elif toks[1] in list(Nicks.nicks.values()):
                        user_id = Nicks.get_user(toks[1])
                    else:
                        await websocket.send("error\nwrong_nick")
                        continue

                    maze_id = Maze.get_maze_id(user_id)
                    world = Maze.get_world(user_id)

                    if not maze_id in list(Maze.mazes.keys()):
                        await websocket.send("error\nwrong_maze_id")
                        continue

                    resp = []

                    resp.append(maze_id)
                    resp.append(str(world))

                    resp.append(str(rp(Maze.mazes[maze_id][world][2])))  # size
                    for r in Maze.mazes[maze_id][world][0]:
                        row = ""
                        for c in r:
                            row += str(c)
                        resp.append(row)

                    # empty color (hex)
                    resp.append(str(Colors.calc_empty(Maze.mazes[maze_id][world][4])))
                    # wall color (hex)
                    resp.append(str(Colors.calc_wall(Maze.mazes[maze_id][world][4])))

                    resp.append(str(Maze.mazes[maze_id][world][3]))  # collected points

                    for user_id in Maze.get_world_users(maze_id, world):
                        data = Maze.player_data[user_id]
                        # usr;[user_id];[nick];[x];[y];[dir][color];[team];[collected_points]
                        resp.append(
                            f"usr;{user_id};{Nicks.get(user_id)};{data[0]};{data[1]};{data[2]};{data[5]};{data[6]};{data[8]}"
                        )

                    for point in Maze.points[maze_id][world]:
                        # point;[x];[y];[color]
                        resp.append(
                            f"point;{rp(point[0])};{rp(point[1])};{Colors.calc_point(point[2])}"
                        )

                    # for key in Maze.keys[maze_id][world]:
                    #    # key;[x];[y];[world to tp];[x to tp];[y to tp]
                    #    resp.append(
                    #        f"key;{rp(key[0])};{rp(key[1])};{key[2]};{rp(key[3])};{rp(key[4])}"
                    #    )

                    for r in resp:
                        print(r)
                    await websocket.send("\n".join(resp).strip("\n"))
                    continue

                resp = Server.handle_cmd(data)
                if resp != "":
                    await websocket.send(resp)

            except KeyboardInterrupt:
                exit()
            # dont care about exceptions, please dont kill me :)
            except websockets.exceptions.ConnectionClosedOK:
                return
            except websockets.exceptions.ConnectionClosedError:
                return
            except websockets.exceptions.ConnectionClosed:
                return


app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def main_page() -> str:
    with open("static/index.htm") as index_file:
        return index_file.read()


if __name__ == "__main__":
    Logger.init()

    Save.init()
    Save.create_backup()
    Save.load_all()

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
