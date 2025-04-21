import threading
import struct
import select
import time
import os
import signal
from fcntl import fcntl, F_GETFL, F_SETFL
from collections import defaultdict

# TODO: replace with static values to avoid string compare and improve performance
KEY_MAPPING = {
    304: "A",
    305: "B",
    306: "Y",
    307: "X",
    308: "L1",
    309: "R1",
    314: "L2",
    315: "R2",
    17: "DY",
    16: "DX",
    310: "SELECT",
    311: "START",
    312: "MENUF",
    114: "V+",
    115: "V-",
}

# Global state with thread-safe access
input_lock = threading.Lock()
active_buttons = defaultdict(bool)
should_exit = False

# Input device configuration
INPUT_DEVICE = "/dev/input/event1"
EVENT_SIZE = 24


def input_worker():
    global active_buttons, should_exit

    fd = os.open(INPUT_DEVICE, os.O_RDWR)
    fcntl(fd, F_SETFL, os.O_NONBLOCK)

    try:
        while not should_exit:
            # Use select with timeout for clean exit
            r, _, _ = select.select([fd], [], [], None)
            if not r:
                continue

            # Read all available events
            data = os.read(fd, EVENT_SIZE * 10)
            for i in range(0, len(data), EVENT_SIZE):
                event = data[i:i + EVENT_SIZE]
                if len(event) < EVENT_SIZE:
                    break

                _, _, ev_type, code, value = struct.unpack("llHHi", event)

                if ev_type != 1 and ev_type != 3:
                    continue

                with input_lock:
                    key = (code, value)
                    if value == 0:
                        # Remove all variants of this key code
                        for k in list(active_buttons.keys()):
                            if k[0] == code:
                                active_buttons[k] = True
                    else:
                        active_buttons[key] = False

    finally:
        os.close(fd)


def start_input_thread():
    thread = threading.Thread(target=input_worker, daemon=True)
    thread.start()
    return thread


def key_pressed(key_code_name, key_value=1):
    target_codes = [code for code, name in KEY_MAPPING.items() if name == key_code_name]

    with input_lock:
        for code in target_codes:
            if (code, key_value) in active_buttons:
                if key_value == 0:
                    del active_buttons[key_value]
                return True
        return False


def reset_input():
    global active_buttons
    with input_lock:
        active_buttons.clear()


def cleanup(signum, frame):
    global should_exit
    should_exit = True


# Set up signal handling for clean exit
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
