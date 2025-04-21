import struct
import select
import time

from collections import defaultdict
from logger import LoggerSingleton as logger

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

# Tracks currently pressed buttons as {(key_code, value): timestamp}
active_buttons = defaultdict(float)


def check_input(device_path="/dev/input/event1"):
    with open(device_path, "rb") as input_file:
        events_processed = 0
        while True:
            r, _, _ = select.select([input_file], [], [], 0)
            if not r:
                break

            event = input_file.read(24)
            if not event or len(event) != 24:
                break

            events_processed += 1
            (_, _, ev_type, key_code, key_value) = struct.unpack("llHHi", event)

            # Only process key events
            if ev_type != 1 and ev_type != 3:
                continue

            # Update state tracking
            key = (key_code, key_value)
            if key_value == 0:
                # Release all variants of this key_code
                for k in list(active_buttons.keys()):
                    if k[0] == key_code:
                        del active_buttons[k]
            else:
                # Press event - update timestamp
                active_buttons[key] = time.time()

        return events_processed > 0


def key_pressed(key_code_name, key_value=1):
    target_codes = [code for code, name in KEY_MAPPING.items() if name == key_code_name]

    for code in target_codes:
        if key_value in (-1, 1):
            return (code, key_value) in active_buttons
    return False


def reset_input():
    active_buttons.clear()