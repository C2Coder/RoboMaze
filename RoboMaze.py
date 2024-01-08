#!/bin/python3
# ========================= LIBRARIES ========================= #
import pygame
import sys
import jacserial
import os
import websockets
import asyncio

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

server_ip = "localhost"
server = "Robo"


class logger:
    logs = []
    file = "logs.txt"
    use = False

    def init():
        if not logger.use:
            return
        if not os.path.isfile(logger.file):
            with open(logger.file, "w") as f:
                f.write("")

    def log(msg):
        if not logger.use:
            return
        logger.logs.append(msg)

    def save_logs():
        if not logger.use:
            return
        with open(logger.file, "a") as f:
            for log in logger.logs:
                f.write(f"{log}\n")
        logger.logs = []


class ws:
    port = 8001

    async def send_cmd(cmd):
        url = f"ws://{server_ip}:{ws.port}"
        async with websockets.connect(url) as webs:
            # Send a greeting message
            await webs.send(cmd)

    async def get_pixels():
        url = f"ws://{server_ip}:{ws.port}"
        async with websockets.connect(url) as webs:
            # Send a greeting message
            await webs.send(f"get_pixels {server}")
            msg = await webs.recv()
            return msg.replace("data:", "")

    async def get_size():
        url = f"ws://{server_ip}:{ws.port}"
        async with websockets.connect(url) as webs:
            # Send a greeting message
            await webs.send(f"get_size {server}")
            msg = await webs.recv()
            return int(msg.replace("size:", ""))


class data:
    window_size = 800
    try:
        size = asyncio.get_event_loop().run_until_complete(ws.get_size())
    except:
        print("\n\nError while connecting to the server!!\n\n")
        exit()


# ============= Usage ============= #


try:
    port = sys.argv[1]
    mode = sys.argv[2]
    baud = 115200

    try:
        if sys.argv[3] == "no-post":
            post = False
    except:
        post = True
except:
    print()
    print(f"Usage python3 RoboPlace.py <port> <Jaculus or Normal> <no-post (optional)>")
    print()
    print(f"Example: python3 RoboPlaceV2.py COM26 Normal no-post")
    print(f"Example: python3 RoboPlaceV2.py /dev/ttyACM0 Jaculus")
    print()
    exit()


if mode == "Jaculus" or mode == "Normal":
    pass
else:
    print("")
    print("Wrong mode")
    print("You selected => " + mode)
    print("Options are => Jaculus or Normal")
    print("")
    pygame.quit()
    exit()

# ========================= GAME class ========================= #


class Game:
    id_timeouts = {}

    timeout_interval = 500  # 500ms

    size = data.size
    window_size = data.window_size

    changes = []

    directions = ["up", "down", "left", "right"]

    def handle_cmds(toks):
        #   toks[0]  toks[1] toks[2] toks[3]
        #    80001    move     up      268
        #     c2c     join    Robo     856
        if toks[-1].isdigit():
            toks.pop()

        user_id = toks[0]
        cmd = toks[1].lower()

        # Handle timeouts
        if (user_id in list(Game.id_timeouts.keys())) and user_id != "C2C":
        #if user_id in Game.id_timeouts:
            return
        else:
            Game.id_timeouts[user_id] = pygame.time.get_ticks()
        try:
            if cmd == "join":
                if len(toks) > 2:
                    maze_id = toks[2]
                    print(f"{user_id} >>> {cmd} {maze_id}")
                    data = f"{user_id} {cmd} {maze_id}"  # c2c join Robo
                else:
                    print(f"{user_id} >>> {cmd}")
                    data = f"{user_id} {cmd}"  # c2c join
                
                logger.log(" ".join(toks))
                asyncio.get_event_loop().run_until_complete(ws.send_cmd(data))
            elif cmd == "move":
                dir = toks[2].lower()
                if dir not in Game.directions:
                    print(f"{user_id} >>> {cmd} {dir} (WRONG DIRECTION)")
                else:
                    print(f"{user_id} >>> {cmd} {dir}")

                    if post:
                        data = f"{user_id} {cmd} {dir}"
                        logger.log(" ".join(toks))
                        asyncio.get_event_loop().run_until_complete(ws.send_cmd(data))

            elif cmd == "test":
                print(f"{user_id} >>> {cmd}")
        except Exception:
            return

    def get_pixels():
        try:
            Game.size = int( (
                asyncio.get_event_loop()
                .run_until_complete(ws.get_size())
            ))

            raw_pixels = (
                asyncio.get_event_loop()
                .run_until_complete(ws.get_pixels())
            )
            Screen.pixels = [
            ["" for i in range(Game.size)] for j in range(Game.size)]
            for y in range(Game.size):
                for x in range(Game.size):
                    Screen.pixels[x][y] = raw_pixels[(y * Game.size) + x]
        except:
            pass


# ========================= SCREEN class ========================= #


class Screen:
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

    DEFAULT_COLOR = "L"

    pixels = []
    pixel_size = int(Game.window_size / Game.size)

    # create array of Game size
    def init():
        Screen.pixels = [
            [Screen.DEFAULT_COLOR for i in range(Game.size)] for j in range(Game.size)
        ]
        Game.get_pixels()

    # draw pixel list to screen
    def update(surface):
        Game.get_pixels()
        Screen.pixel_size = int(Game.window_size / Game.size)
        for y in range(Game.size):
            for x in range(Game.size):
                pygame.draw.rect(
                    surface,
                    pygame.Color(
                        Screen.colors[Screen.chars.index(Screen.pixels[x][y])]
                    ),
                    (
                        x * Screen.pixel_size,
                        y * Screen.pixel_size,
                        Screen.pixel_size,
                        Screen.pixel_size,
                    ),
                )


# ========================= Functions ========================= #


def parse(input):
    data = input.split(" ")
    if len(data) < 2:
        return None
    return data


# ========================= Main Loop ========================= #


def main():
    # Initialize pygame

    screen = pygame.display.set_mode([Game.window_size, Game.window_size])
    pygame.init()

    pygame.display.set_caption("RoboMaze")
    pygame.font.init()

    Screen.init()
    Screen.update(screen)
    pygame.display.flip()

    logger.init()

    # Variable to keep the main loop running
    running = True

    pygame.time.set_timer(pygame.USEREVENT, 500)  # every 5s
    pygame.time.set_timer(pygame.USEREVENT_DROPFILE, 100)  # every 100 ms

    # serial setup

    with jacserial.Serial(port, baud, timeout=0) as jac:
        while running:
            event = pygame.event.wait()
            # Did the user hit a key?

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

            # Did the user click the window close button? If so, stop the loop.
            elif event.type == QUIT:
                running = False
                # Every 100 ms
            elif event.type == pygame.USEREVENT_DROPFILE:
                while True:
                    # read serial
                    if mode == "Jaculus":
                        line = jac.readline_jac()
                    elif mode == "Normal":
                        line = jac.readline()
                    if len(line) == 0:
                        break  # break from loop
                    toks = parse(line)
                    if toks is None:
                        continue  # next loop
                    Game.handle_cmds(toks)

                # Every 5s
            elif event.type == pygame.USEREVENT:
                logger.save_logs()
                # Screen.draw_changes()
                
                Screen.update(screen)
                pygame.display.flip()
                ticks = pygame.time.get_ticks()
                for id in list(Game.id_timeouts.keys()):
                    if Game.id_timeouts[id] < ticks - Game.timeout_interval:
                        Game.id_timeouts.pop(id)
                        # print(f'ID {id} is removed from timeouts')
        # close Game
        pygame.quit()
        exit()


#asyncio.get_event_loop().run_until_complete(ws.send_cmd(f"C2C join {server}"))
asyncio.get_event_loop().run_until_complete(ws.send_cmd(f"C2C join Robo"))
# call main function
main()
