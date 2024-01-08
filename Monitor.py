#!/bin/python3
# ========================= LIBRARIES ========================= #
import pygame
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
            return msg

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


# ========================= GAME class ========================= #


class Game:
    size = data.size
    window_size = data.window_size

    def get_pixels():
        try:
            raw_pixels = (
                asyncio.get_event_loop()
                .run_until_complete(ws.get_pixels())
                .replace("data:", "")
            )

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




# ========================= Main Loop ========================= #


def main():
    # Initialize pygame

    screen = pygame.display.set_mode([Game.window_size, Game.window_size])
    pygame.init()

    pygame.display.set_caption("RoboMaze - Monitor")
    pygame.font.init()

    Screen.init()
    Screen.update(screen)
    pygame.display.flip()

    # Variable to keep the main loop running
    running = True

    pygame.time.set_timer(pygame.USEREVENT, 5000)  # every 5 s

    # serial setup

    while running:
        event = pygame.event.wait()
        # Did the user hit a key?
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False
        # Did the user click the window close button? If so, stop the loop.
        elif event.type == QUIT:
            running = False
            # Every 5s
        elif event.type == pygame.USEREVENT:
            Game.get_pixels()
            Screen.update(screen)
            pygame.display.flip()
    # close Game
    pygame.quit()
    exit()


# call main function
main()
