import struct
import select
import os
import time

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

current_code = 0
current_code_name = ""
current_value = 0

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

    # Backward compatibility - open the file if not already open
    if input_file is None:
        init_input(device_path)
        if input_file is None:
            return False

    try:
        # Use select with a very short timeout (50ms)
        r, _, _ = select.select([input_file], [], [], 0.05)

        if r:  # If input is available
            event = input_file.read(24)
            if event and len(event) == 24:  # Make sure we read complete event
                _, _, _, key_code, key_value = struct.unpack("llHHI", event)
                if key_value != 0:
                    if key_value != 1:
                        key_value = -1
                    current_code = key_code
                    current_code_name = KEY_MAPPING.get(current_code, str(current_code))
                    current_value = key_value
                    logger.log_debug(
                        f"Key pressed: {current_code_name}, value: {current_value}"
                    )
                    return True
    except Exception as e:
        # Handle errors gracefully - don't crash
        print(f"Input error: {e}")
        # Try to recover by reopening the file
        try:
            if input_file:
                input_file.close()
            input_file = None
            time.sleep(0.1)  # Brief pause before retry
        except:
            pass

    return False


def cleanup_input():
    global input_file
    if input_file:
        try:
            input_file.close()
        except:
            pass
        input_file = None


def key_pressed(key_code_name, key_value=99):
    if current_code_name == key_code_name:
        if key_value != 99:
            return current_value == key_value
        return True


def reset_input():
    global current_code_name, current_value
    current_code_name = ""
    current_value = 0
    logger.log_debug("Input reset")
