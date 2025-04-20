import struct
import select
import os
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
input_file = None


def init_input(device_path="/dev/input/event1"):
    global input_file
    try:
        input_file = open(device_path, "rb")
        # Set non-blocking mode
        fd = input_file.fileno()
        flags = os.fcntl.fcntl(fd, os.fcntl.F_GETFL)
        os.fcntl.fcntl(fd, os.fcntl.F_SETFL, flags | os.O_NONBLOCK)
        return True
    except Exception as e:
        print(f"Failed to initialize input: {e}")
        return False


def check_input(device_path="/dev/input/event1"):
    global current_code, current_code_name, current_value, input_file

    if input_file is None:
        if not init_input(device_path):
            return False

    try:
        events_processed = 0
        while True:  # Process all available events
            r, _, _ = select.select([input_file], [], [], 0)
            if not r:
                break

            event = input_file.read(24)
            if not event or len(event) != 24:
                break

            events_processed += 1

            # Parse event
            _, _, _, key_code, key_value = struct.unpack("llHHI", event)

            # Normalize value while preserving -1/1 distinction
            normalized_value = 0
            if key_value == 1:
                normalized_value = 1
            elif key_value > 1:  # Handle analog triggers or pressure-sensitive buttons
                normalized_value = -1 if key_value < 0 else 1

            # Update state tracking
            key = (key_code, normalized_value)
            if normalized_value == 0:
                # Release all variants of this key_code
                for k in list(active_buttons.keys()):
                    if k[0] == key_code:
                        del active_buttons[k]
            else:
                # Press event - update timestamp
                active_buttons[key] = time.time()

        return events_processed > 0

    except Exception as e:
        print(f"Input error: {e}")
        cleanup_input()
        time.sleep(0.1)
        init_input(device_path)
        return False


def key_pressed(key_code_name, key_value=1):  # Changed default to 1
    # Find matching key codes
    target_codes = [code for code, name in KEY_MAPPING.items() if name == key_code_name]

    # Check all possible code/value combinations
    for code in target_codes:
        # Handle both specified value and default (1)
        check_values = [key_value] if key_value in (-1, 1) else [-1, 1]

        for value in check_values:
            if (code, value) in active_buttons:
                return True
    return False


def reset_input():
    active_buttons.clear()


def cleanup_input():
    global input_file
    if input_file:
        try:
            input_file.close()
        except:
            pass
        input_file = None