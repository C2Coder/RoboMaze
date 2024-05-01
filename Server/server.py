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
import hashlib
import math
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

    def calc_empty(world_color):
        return Colors.lighten_color(world_color, factor=0.9)

    def calc_wall(world_color):
        return Colors.darken_color(world_color, factor=0.85)

    def rand_player_color(user_id: str):
        random.seed(int(hashlib.md5(user_id.encode()).hexdigest(), 16))
        return Colors.lighten_color(
            Colors.player_colors[random.randint(0, len(Colors.player_colors) - 1)], 0.35
        )

    def calc_point(point_value):  # TODO - REWRITE
        return "#D0A000"

    def calc_key(world: int):
        return Colors.darken_color(Colors.world_colors[world], 0.2)  # TODO - ADD CHECK

    def world_color(world: int):
        return Colors.world_colors[world]  # TODO - ADD CHECK

    world_colors = [
        "#eeeeee",
        "#ff00ff",
        "#ff0000",
        "#ffff00",
        "#00ff00",
        "#00ffff",
        "#0000ff",
    ]

    player_colors = [
        "#ff3200",
        "#ff6600",
        "#ffcc00",
        "#cbff00",
        "#99ff00",
        "#65ff00",
        "#33ff00",
        "#00ff00",
        "#00ff32",
        "#00ff66",
        "#00ff99",
        "#00ffcb",
        "#00cbff",
        "#0099ff",
        "#0066ff",
        "#0033ff",
        "#3200ff",
        "#6500ff",
        "#9900ff",
        "#cc00ff",
        "#ff00cb",
        "#ff0098",
        "#ff0066",
        "#ff0033",
    ]


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

    mazes = {}  # maze_id:[[maze[][], level, size, collected points, maze_color (hex)]]
    points = {}  # maze_id:[world:[[x, y, value]]]
    keys = {}  # maze_id: [world:[[color, x, y, world_to_tp, x_to_tp, y_to_tp]]]
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
            Colors.rand_player_color(user_id),  # color
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
            print("Gen via join")
            Maze.gen_maze(maze_id, Config.default_level, world)
            Maze.render(maze_id, world)
            Maze.gen_points(maze_id, world)
            Maze.gen_keys(maze_id)

        # edit the player data
        Maze.player_data[user_id] = [
            rp(random.randint(0, Maze.mazes[maze_id][world][2] - 1)),  # X
            rp(random.randint(0, Maze.mazes[maze_id][world][2] - 1)),  # Y
            0,  # direction
            maze_id,  # maze_id
            world,  # world_id
            Colors.rand_player_color(user_id),  # color
            user_id,  # team (default team is your user_id)
            time.time(),  # last time played
            Maze.player_data[user_id][8],  # num of points
        ]

    def move_player(user_id: str, dir: str) -> None:
        if not user_id in list(Maze.player_data.keys()):
            print(f"Playerdata of user {user_id} not found")
            return

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

                elif any(
                    [Maze.player_data[user_id][0], Maze.player_data[user_id][1] - 1]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0],
                                Maze.player_data[user_id][1] - 1,
                            ]
                            == sublist[1:3]
                        ][0],
                    )

            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] + 1] == "w":
                    Maze.player_data[user_id][1] += 1  # Y

                elif any(
                    [Maze.player_data[user_id][0], Maze.player_data[user_id][1] + 1]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0],
                                Maze.player_data[user_id][1] + 1,
                            ]
                            == sublist[1:3]
                        ][0],
                    )

        elif rot == 1:  # right
            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0] + 1][data[1]] == "w":
                    Maze.player_data[user_id][0] += 1  # X

                elif any(
                    [Maze.player_data[user_id][0] + 1, Maze.player_data[user_id][1]]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0] + 1,
                                Maze.player_data[user_id][1],
                            ]
                            == sublist[1:3]
                        ][0],
                    )
            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0] - 1][data[1]] == "w":
                    Maze.player_data[user_id][0] -= 1  # X

                elif any(
                    [Maze.player_data[user_id][0] - 1, Maze.player_data[user_id][1]]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0] - 1,
                                Maze.player_data[user_id][1],
                            ]
                            == sublist[1:3]
                        ][0],
                    )

        elif rot == 2:  # down
            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] + 1] == "w":
                    Maze.player_data[user_id][1] += 1  # Y

                elif any(
                    [Maze.player_data[user_id][0], Maze.player_data[user_id][1] + 1]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0],
                                Maze.player_data[user_id][1] + 1,
                            ]
                            == sublist[1:3]
                        ][0],
                    )

            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0]][data[1] - 1] == "w":
                    Maze.player_data[user_id][1] -= 1  # Y

                elif any(
                    [Maze.player_data[user_id][0], Maze.player_data[user_id][1] - 1]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0],
                                Maze.player_data[user_id][1] - 1,
                            ]
                            == sublist[1:3]
                        ][0],
                    )

        elif rot == 3:  # left
            if dir == "forward":
                if not Maze.pixels[maze_id][world][data[0] - 1][data[1]] == "w":
                    Maze.player_data[user_id][0] -= 1  # X

                elif any(
                    [Maze.player_data[user_id][0] - 1, Maze.player_data[user_id][1]]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0] - 1,
                                Maze.player_data[user_id][1],
                            ]
                            == sublist[1:3]
                        ][0],
                    )

            elif dir == "backward":
                if not Maze.pixels[maze_id][world][data[0] + 1][data[1]] == "w":
                    Maze.player_data[user_id][0] += 1  # X

                elif any(
                    [Maze.player_data[user_id][0] + 1, Maze.player_data[user_id][1]]
                    == sublist[1:3]
                    for sublist in Maze.keys[maze_id][world]
                ):
                    Maze.tp_player(
                        user_id,
                        [
                            sublist
                            for sublist in Maze.keys[maze_id][world]
                            if [
                                Maze.player_data[user_id][0] + 1,
                                Maze.player_data[user_id][1],
                            ]
                            == sublist[1:3]
                        ][0],
                    )

    def rotate_player(user_id: str, dir: str) -> None:
        if not user_id in list(Maze.player_data.keys()):
            print(f"Playerdata of user {user_id} not found")
            return
        if dir == "left":
            Maze.player_data[user_id][2] -= 1
        elif dir == "right":
            Maze.player_data[user_id][2] += 1

        if Maze.player_data[user_id][2] < 0:
            Maze.player_data[user_id][2] = 3
        elif Maze.player_data[user_id][2] > 3:
            Maze.player_data[user_id][2] = 0

    def tp_player(user_id: str, key: list):
        data = key[3:]

        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for d in dirs:
            try:

                if (
                    Maze.pixels[Maze.player_data[user_id][3]][data[0]][data[1] + d[0]][
                        data[2] + d[1]
                    ]
                    == "e"
                ):
                    Maze.player_data[user_id][0] = data[1] + d[0]  # x
                    Maze.player_data[user_id][1] = data[2] + d[1]  # y
                    Maze.player_data[user_id][4] = data[0]  # world
                    break
            except KeyboardInterrupt:
                quit()

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
                # print(f"user: {user_id} is on point")
                Maze.points[maze_id][world].pop(i)
                Maze.mazes[maze_id][world][3] += p[2]
                if Config.dgkops and maze_id == Config.public_server:
                    Maze.gen_points(maze_id, world, removed_point=p_pos)
                Maze.try_lvlup(maze_id, world)
                return True
        return False

    def try_lvlup(maze_id: str, world: int) -> None:
        cur_lvl = Maze.mazes[maze_id][world][1]
        points_to_lvlup = Maze.calc_lvlup_point(cur_lvl)

        if maze_id == Config.public_server:
            points_to_lvlup = points_to_lvlup * 2

        if Maze.mazes[maze_id][world][3] >= points_to_lvlup:
            Maze.mazes[maze_id][world][3] = 0  # set collected points to 0
            Maze.mazes[maze_id][world][1] += 1  # level + 1
            Maze.gen_maze(maze_id, Maze.mazes[maze_id][world][1], world)
            Maze.render(maze_id, world)
            Maze.gen_points(maze_id, world)
            Maze.gen_keys(maze_id)

        elif len(Maze.points[maze_id][world]) == 0:
            Maze.gen_points(maze_id, world)

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

        if not maze_id in list(Maze.points.keys()):
            Maze.points[maze_id] = []
        while len(Maze.points[maze_id]) <= world + 1:
            Maze.points[maze_id].append([])

        count = len(Maze.points[maze_id][world])
        tmp = list(Maze.points[maze_id][world])

        for _ in range(points_on_lvl - count):
            tmp.append(Maze._gen_point(maze_id, world, level, len(tmp), removed_point))

        Maze.points[maze_id][world] = tmp.copy()

    def _rand_key_pos(maze_id: str, world: int):

        if len(Maze.mazes[maze_id]) <= world or len(Maze.mazes[maze_id][world]) < 2:
            Maze.gen_maze(maze_id, Config.default_level, world)
            Maze.render(maze_id, world)
            Maze.gen_points(maze_id, world)
            # Maze.gen_keys(maze_id)

        maze = Maze.pixels[maze_id][world]
        size = rp(Maze.mazes[maze_id][world][2])

        empty_spots = []
        for x in range(size):
            for y in range(size):
                if maze[x][y] == "e":  # Empty spot
                    empty_spots.append((x, y))

        options = []
        for i, j in empty_spots:
            for x, y in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
                if 0 <= x < len(maze) and 0 <= y < len(maze[0]) and maze[x][y] == "w":
                    options.append((x, y))

        choice = random.choice(options)

        if any(choice == sublist[1:3] for sublist in Maze.keys[maze_id][world]):
            return Maze._rand_key_pos(maze_id, world)
        else:
            return choice

    def gen_key_pair(maze_id: str, world_1: int, world_2: int) -> None:

        while len(Maze.keys[maze_id]) <= max(world_1, world_2) + 1:
            Maze.keys[maze_id].append([])

        pos1 = Maze._rand_key_pos(maze_id, world_1)
        pos2 = Maze._rand_key_pos(maze_id, world_2)

        Maze.keys[maze_id][world_1].append(
            [Colors.calc_key(world_2), pos1[0], pos1[1], world_2, pos2[0], pos2[1]]
        )
        Maze.keys[maze_id][world_2].append(
            [Colors.calc_key(world_1), pos2[0], pos2[1], world_1, pos1[0], pos1[1]]
        )

    def gen_keys(maze_id: str):
        Maze.keys[maze_id] = []  # wipe keys

        #                      world  world
        Maze.gen_key_pair(maze_id, 0, 1)  # TEST
        Maze.gen_key_pair(maze_id, 1, 3)  # TEST
        Maze.gen_key_pair(maze_id, 3, 6)  # TEST
        Maze.gen_key_pair(maze_id, 6, 2)  # TEST
        Maze.gen_key_pair(maze_id, 2, 5)  # TEST
        Maze.gen_key_pair(maze_id, 5, 4)  # TEST
        Maze.gen_key_pair(maze_id, 1, 5)  # TEST

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

            if len(Maze.mazes[maze_id][world]) > 1:
                Maze.mazes[maze_id][world] = [
                    maze,
                    level,
                    size,
                    Maze.mazes[maze_id][world][3],
                    Maze.mazes[maze_id][world][4],
                ]
            else:
                Maze.mazes[maze_id][world] = [
                    maze,
                    level,
                    size,
                    0,
                    Colors.world_color(world),
                ]  # TODO - ADD COLOR BASED ON WORLD
        else:
            Maze.mazes[maze_id] = [[] for _ in range(world + 1)]
            Maze.mazes[maze_id][world] = [
                maze,
                level,
                size,
                0,
                Colors.world_color(world),
            ]  # TODO - ADD COLOR BASED ON WORLD

    def render(maze_id: str, world: int) -> None:
        size = Maze.mazes[maze_id][world][2]
        world_color = Maze.get_world_color(maze_id, world)

        if not maze_id in list(Maze.pixels.keys()):
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
                    pixels[y][x] = "w"  # idk why but it works now so dont touch it

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

        if x < rp(Maze.mazes[maze_id][world][2]):
            p_right = int(Maze.mazes[maze_id][world][0][x + 1][y])
        else:
            p_right = 1  # wall

        if y > 0:
            p_up = int(Maze.mazes[maze_id][world][0][x][y - 1])
        else:
            p_up = 1  # wall

        if y < rp(Maze.mazes[maze_id][world][2]):
            p_down = int(Maze.mazes[maze_id][world][0][x][y + 1])
        else:
            p_down = 1  # wall

        sens = 0

        if dir == 0:  # facing up
            sens += 1 * p_up
            sens += 2 * p_right
            sens += 4 * p_down
            sens += 8 * p_left
        elif dir == 1:  # facing right
            sens += 1 * p_right
            sens += 2 * p_down
            sens += 4 * p_left
            sens += 8 * p_up
        elif dir == 2:  # facing down
            sens += 1 * p_down
            sens += 2 * p_left
            sens += 4 * p_right
            sens += 8 * p_up
        elif dir == 3:  # facing left
            sens += 1 * p_left
            sens += 2 * p_up
            sens += 4 * p_right
            sens += 8 * p_down

        min_distance = float("inf")
        closest_key = None

        for key in [sublist[1:3] for sublist in Maze.keys[maze_id][world]]:
            x_k, y_k = key
            dist = math.sqrt((x_k - x) ** 2 + (y_k - y) ** 2)
            if dist < min_distance:
                min_distance = dist
                closest_key = key

        x_key, y_key = closest_key

        min_distance = float("inf")
        closest_point = None

        for point in [sublist[:2] for sublist in Maze.points[maze_id][world]]:
            x_p, y_p = point
            dist = math.sqrt((x_p - x) ** 2 + (y_p - y) ** 2)
            if dist < min_distance:
                min_distance = dist
                closest_point = key

        x_point, y_point = closest_point

        #        8      1     1   1      1         1        1       1      1     1      = 17/22
        # <id> <nick> <size> <x> <y> <x_point> <y_point> <x_key> <y_key> <dir> <sens>

        out.append("_r_")  # random string so i can handle it differently

        out.append(str(message_id))  # id
        out.append(str(nick))  # nick
        out.append(str(rp(Maze.mazes[maze_id][world][2])))  # size
        out.append(str(x))  # x
        out.append(str(y))  # y

        out.append(str(x_point))  # x_point
        out.append(str(y_point))  # y_point

        out.append(str(x_key))  # x_key
        out.append(str(y_key))  # y_key

        out.append(str(dir))  # dir

        out.append(str(sens))  # sens

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
        if not Save.folder.replace("/", "") in os.listdir():
            os.mkdir(Save.folder)

        if not Save.backup_folder.replace("/", "") in os.listdir():
            os.mkdir(Save.backup_folder)

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

                tmp.append(f"{' '*4}keys pos:")
                _tmp = ""
                if maze_id in list(Maze.keys.keys()):
                    for p in Maze.keys[maze_id][world]:
                        _tmp += f"({p[0]}, {p[1]}, {p[2]}, {p[3]}, {p[4]}, {p[5]});"
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
            elif "keys pos:" in lines[i]:
                i += 1
                if not maze_id in list(Maze.keys.keys()):
                    Maze.keys[maze_id] = []

                while len(Maze.keys[maze_id]) <= world:
                    Maze.keys[maze_id].append([])

                Maze.keys[maze_id][world] = []

                for p in (
                    lines[i]
                    .replace(" ", "")
                    .replace(")", "")
                    .replace("(", "")
                    .split(";")
                ):
                    Maze.keys[maze_id][world].append([int(n) for n in p.split(",")])
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
    port = 8888
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

            if (not user_id in list(Maze.player_data.keys())) and cmd != "join":
                print(f"Playerdata of user {user_id} not found")
                return ""

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

                    for key in Maze.keys[maze_id][world]:
                        # key;[x_full];[y_full];[world to tp];[x_full to tp];[y_full to tp]
                        resp.append(f"key;{key[0]};{key[1]};{key[2]};{key[3]};{key[4]}")

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
        Maze.render(Config.public_server, Config.default_world)
        Maze.gen_points(Config.public_server, Config.default_world)
        Maze.gen_keys(Config.public_server)

    Server.edit_script()

    bg_t = threading.Thread(target=Server.background_func)
    bg_t.start()

    loop = threading.Thread(target=Server.loop)
    loop.start()

    start_server = websockets.serve(WS.handler, "0.0.0.0", WS.port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
