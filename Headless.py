#!/bin/python3
# ========================= LIBRARIES ========================= #
import sys
import serial
import os
import websocket
import time
import threading

from jacprotocol import jp

server_ip = "localhost"
server = "Robo"

admin_MACs = ["serial", "34:85:18:82:4a:b2"]


# ============= Usage ============= #


try:
    port = sys.argv[1]
    mode = sys.argv[2]
    # baud = 115200
    baud = 921600
except:
    print("")
    print(f"Usage python3 Headless.py <port> <Jaculus or Normal>")
    print("")
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


class nicks:
    file = "data/nicks.txt"

    nicks = {}

    def load():
        with open(nicks.file, "r") as f:
            lines = f.readlines()

        for line in lines:
            toks = line.split(";", 1)
            if not len(toks) == 2:
                continue

            nicks.nicks[toks[0]] = toks[1]

    def save():
        lines = []

        for real_name in nicks.nicks:
            lines.append(f"{real_name};{nicks.nicks[real_name]}\n")

        with open(nicks.file, "w") as f:
            f.writelines(lines)

    def get(user_id: str) -> str:
        if user_id in list(nicks.nicks.keys()):
            return nicks.nicks[user_id]
        return user_id

    def set_nick(user_id: str, nick: str):
        nicks.nicks[user_id] = nick


class ws:
    port = 8001

    url = ""
    socket = None

    def connect():
        ws.url = f"ws://{server_ip}:{ws.port}"
        ws.socket = websocket.WebSocket()
        ws.socket.connect(ws.url)
        ws.socket.settimeout(30)

    def send(string):
        ws.socket.send(string)

    def get_data():
        return ws.socket.recv()

    def ping_loop():
        while True:
            ws.send("ping")
            time.sleep(20)


# ========================= GAME class ========================= #


class Game:
    id_timeouts = {}

    timeout_interval = 1  # 5s

    changes = []

    to_serial = []

    to_handle = []

    running = True

    directions = ["forward", "backward", "left", "right"]

    def send_to_serial(ser):
        for s in Game.to_serial:
            for c in s:
                jp.put(ord(c))

            jp.put(ord("\n"))

            ser.write(jp.serialize(16))

        Game.to_serial = []

    def handle_cmds(toks) -> None:
        #   toks[0]  toks[1] toks[2]
        #    C2C      move     up

        if toks[0] == "_r_":  # random string so i can handle it differently
            _, user_id, message_id, left, front, right, x, y, dir, team, num_of_points = toks
            Game.to_serial.append(f"{message_id} {user_id}_{left}{front}{right}{dir}")

            return

        user_id = toks[0]
        cmd = toks[1].lower()

        message_id = int(toks[-1])

        # Handle timeouts
        if user_id in admin_MACs:
            pass
        elif user_id in list(Game.id_timeouts):
            return
        else:
            Game.id_timeouts[user_id] = time.time()

        nick = nicks.get(user_id)

        try:
            if cmd == "join":
                if len(toks) > 3:
                    maze_id = toks[2]

                    print(f"{nick} >>> {cmd} {maze_id}")
                    data = f"{user_id} {nick} {cmd} {maze_id} {message_id}"
                else:
                    print(f"{nick} >>> {cmd}")
                    data = f"{user_id} {nick} {cmd} {message_id}"

                logger.log(data)
                ws.send(data)

            elif cmd == "move":
                dir = toks[2].lower()
                if dir not in Game.directions:
                    print(f"{nick} >>> {cmd} {dir} (WRONG DIRECTION)")
                else:
                    print(f"{nick} >>> {cmd} {dir}")

                    data = f"{user_id} {nick} {cmd} {dir} {message_id}"
                    logger.log(data)
                    ws.send(data)

            elif cmd == "rotate":
                dir = toks[2].lower()
                if dir not in Game.directions:
                    print(f"{nick} >>> {cmd} {dir} (WRONG DIRECTION)")
                else:
                    print(f"{nick} >>> {cmd} {dir}")

                    data = f"{user_id} {nick} {cmd} {dir} {message_id}"
                    logger.log(data)
                    ws.send(data)

            elif cmd == "setname":
                new_nick = toks[2]
                nicks.set_nick(user_id, new_nick)
                print(f"{nick} >>> {cmd} {new_nick}")

            elif cmd == "test":
                print(f"{nick} >>> {cmd}")

            elif cmd == "print":  # TEMP
                print(f"{nick} >>> {' '.join(toks[2:-1])}")
        except Exception:
            return

    def handle_data():
        for line in Game.to_handle:
            line = line.strip()
            if len(line) == 0:
                continue  # break from loop

            toks = parse(line)
            if toks is None:
                continue  # next loop

            Game.handle_cmds(toks)
        Game.to_handle = []


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
    threading.Timer(5, timeout_loop).start()


def serial_loop():

    # Variable to keep the main loop running

    last_time = time.time()
    # serial setup

    with serial.Serial(port, baud, timeout=0) as ser:
        while Game.running:
            cur_time = time.time()
            if cur_time - last_time > 0.1:
                last_time = cur_time
                while True:
                    if mode == "Jaculus":
                        b = ser.read_all()
                        l = list(b)

                        if len(l) == 0:
                            break  # exit loop

                        while True:
                            try:
                                if len(l) == 0:
                                    break

                                size = l[1]

                                packet = list(l[0 : size + 2])
                                for _ in range(size + 2):
                                    l.pop(0)

                                # get the parts of the packet

                                # delimeter = packet[0] # not needed ...
                                # size = packet[1]
                                # idk_what_is_this = packet[2]
                                channel = packet[3]
                                data = packet[4:-2]
                                # chksm_in = packet[-2:]

                                # get the checksum
                                for d in data:
                                    jp.put(d)

                                test_packet = jp.serialize(channel)
                                if packet != test_packet:
                                    continue

                                tmp = ""
                                for d in data:
                                    tmp += chr(d)
                                Game.to_handle.append(tmp)

                            except:
                                pass

                    elif mode == "Normal":
                        Game.to_handle.append(ser.read_all().decode())

                Game.handle_data()

                Game.send_to_serial(ser)

        # close Game
        exit()


def receive_loop():
    while True:
        recieved = ws.get_data()
        Game.to_handle.append(recieved)


if __name__ == "__main__":
    ws.connect()

    ping_t = threading.Thread(target=ws.ping_loop)
    ping_t.start()

    recieve_t = threading.Thread(target=receive_loop)
    recieve_t.start()

    serial_t = threading.Thread(target=serial_loop)
    serial_t.start()

    # logger.init()
#
# asyncio.get_event_loop().run_until_complete(receive_data(ws.socket))
