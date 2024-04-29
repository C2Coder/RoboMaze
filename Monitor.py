#!/bin/python3
# ========================= LIBRARIES ========================= #
import pygame
import websockets
import asyncio
import sys

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

# ============= Usage ============= #

server_ip = "localhost"

try:
    user = sys.argv[1]
except:
    print()
    print(
        f"Usage python3 Monitor.py <user>"
    )
    print()
    print(f"Example: python3 Monitor.py Nekdo123")
    print()
    exit()

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
            await webs.send(f"get_pixels {user}")
            msg = await webs.recv()
            return msg

    async def get_size():
        url = f"ws://{server_ip}:{ws.port}"
        async with websockets.connect(url) as webs:
            # Send a greeting message
            await webs.send(f"get_size {user}")
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
    colors = {
    "a":"#ffff50", # \
    "b":"#99ff00", # |
    "c":"#00ff99", # |
    "e":"#0099ff", # |
    "f":"#3300ff", # |  Used for Players
    "g":"#9900ff", # |
    "h":"#ff00ff", # |
    "i":"#ff0099", # |
    "j":"#ff3300", # |
    "k":"#ff6600", # /

    "A":"#ff0000", # \
    "B":"#ffff00", # |
    "C":"#00ff00", # |  Used for keys
    "D":"#00ffff", # |
    "E":"#0000ff", # /

    "F":"#222222",
    "G":"#440000",
    "H":"#444400",
    "I":"#004400",
    "J":"#004444",
    "K":"#000044",

    "L":"#ffffff",
    "M":"#ffaaaa",
    "N":"#ffffaa",
    "O":"#aaffaa",
    "P":"#aaffff",
    "Q":"#aaaaff",

    "X":"#D0A000", # Point

    }

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
                        Screen.colors[Screen.pixels[x][y]]
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

    pygame.time.set_timer(pygame.USEREVENT, 50)  # every 5 s

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
