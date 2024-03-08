#!/bin/python3
# ========================= LIBRARIES ========================= #
import sys
import jacserial
import os
import websockets
import asyncio
import time
import threading

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards

server_ip = "localhost"
server = "Robo"

admin_MACs = []

class logger:
    logs = []
    file = "logs.txt"
    use = True

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

# ============= Usage ============= #


try:
    port = sys.argv[1]
    mode = sys.argv[2]
    baud = 115200

except:
    print()
    print(f"Usage python3 Headless.py <port> <Jaculus or Normal>")
    print()
    print(f"Example: python3 Headless.py COM26 Normal")
    print(f"Example: python3 Headless.py /dev/ttyACM0 Jaculus")
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
    exit()

# ========================= GAME class ========================= #


class Game:
    id_timeouts = {}

    timeout_interval = 5000  # 5s

    changes = []

    directions = ["up", "down", "left", "right"]

    def handle_cmds(toks):
        #   toks[0]  toks[1] toks[2]
        #    80001    move    up
        user_id = toks[0]
        cmd = toks[1].lower()

        # Handle timeouts
        if user_id in list(Game.id_timeouts) and not user_id in admin_MACs:
            return
        else:
            Game.id_timeouts[user_id] = time.time()
        try:
            if cmd == "join":
                if len(toks) > 2:
                    maze_id = toks[2]

                    print(f"{user_id} >>> {cmd} {maze_id}")
                    data = f"{user_id} {cmd} {maze_id}"
                else:
                    print(f"{user_id} >>> {cmd}")
                    data = f"{user_id} {cmd}"
                
                logger.log(data)
                asyncio.get_event_loop().run_until_complete(ws.send_cmd(data))
            elif cmd == "move":
                dir = toks[2].lower()
                if dir not in Game.directions:
                    print(f"{user_id} >>> {cmd} {dir} (WRONG DIRECTION)")
                else:
                    print(f"{user_id} >>> {cmd} {dir}")

                    data = f"{user_id} {cmd} {dir}"
                    logger.log(data)
                    asyncio.get_event_loop().run_until_complete(ws.send_cmd(data))

            elif cmd == "test":
                print(f"{user_id} >>> {cmd}")
        except Exception:
            return


# ========================= Functions ========================= #


def parse(input):
    data = input.split(" ")
    if len(data) < 2:
        return None
    return data


# ========================= Main Loop ========================= #


def timeout_loop():
    logger.save_logs()
    ticks = time.time()
    for id in list(Game.id_timeouts.keys()):
        if Game.id_timeouts[id] < ticks - Game.timeout_interval:
            Game.id_timeouts.pop(id)
            # print(f'ID {id} is removed from timeouts')
    threading.Timer(5, timeout_loop).start()

def main():
    logger.init()

    # Variable to keep the main loop running
    running = True
    last_time = time.time()
    # serial setup

    with jacserial.Serial(port, baud, timeout=0) as jac:
        while running:
            cur_time = time.time()
            if cur_time-last_time > 0.1:
                last_time = cur_time
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

        # close Game
        exit()


#asyncio.get_event_loop().run_until_complete(ws.send_cmd(f"C2C join {server}"))
asyncio.get_event_loop().run_until_complete(ws.send_cmd(f"C2C join Robo"))
# call main function
main()
