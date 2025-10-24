import jds6600
import serial

import time

import matplotlib.pyplot as plt


def parse_frequency(response: str) -> float:
    """
    Extracts the frequency value from a LeCroy 9300 PAVA response string.

    Example input:
        'C1:PAVA FREQ,10.00175E+3 HZ,AV'
    Returns:
        10001.75
    """
    # Split by commas
    parts = response.split(',')
    if len(parts) < 2:
        raise ValueError("Unexpected response format")

    # The numeric value is in the second part
    value_str = parts[1].split()[0]  # '10.00175E+3'

    # Convert to float
    frequency = float(value_str)
    return frequency


def get_freq(serial, retries=3, delay=0.5):
    """
    Reads the amplitude from the scope via RS-232.

    serial: an open pyserial Serial object
    retries: number of times to retry on failure
    delay: seconds to wait between retries
    """
    for attempt in range(1, retries + 1):
        try:
            # Send command
            serial.write(b"parameter_value? freq\r")

            # Read echoed command
            echo = serial.read_until(b'\r', size=None)  # uses port timeout
            if not echo:
                raise TimeoutError("No echo received from scope")
            print("Echo:", echo.decode().strip())

            # Read actual response
            response = serial.read_until(b'\r', size=None)  # uses port timeout
            if not response:
                raise TimeoutError("No response received from scope")
            print("Response:", response.decode().strip())

            # Parse numeric value (replace with your actual parser)
            return parse_frequency(response.decode().strip())

        except (TimeoutError, ValueError) as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to get amplitude after {retries} attempts") from e

    return 1.0


def get_ampl(serial, retries=3, delay=0.5):
    """
    Reads the amplitude from the scope via RS-232.

    serial: an open pyserial Serial object
    retries: number of times to retry on failure
    delay: seconds to wait between retries
    """
    for attempt in range(1, retries + 1):
        try:
            # Send command
            serial.write(b"parameter_value? ampl\r")

            # Read echoed command
            echo = serial.read_until(b'\r', size=None)  # uses port timeout
            if not echo:
                raise TimeoutError("No echo received from scope")
            print("Echo:", echo.decode().strip())

            # Read actual response
            response = serial.read_until(b'\r', size=None)  # uses port timeout
            if not response:
                raise TimeoutError("No response received from scope")
            print("Response:", response.decode().strip())

            # Parse numeric value (replace with your actual parser)
            return parse_frequency(response.decode().strip())

        except (TimeoutError, ValueError) as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to get amplitude after {retries} attempts") from e

    return 1.0


def send_query(serial, command):
    """
    Sends a command to the scope and returns the raw response line.
    Clears buffer first to avoid leftover echoes.
    """
    serial.reset_input_buffer()  # clear any leftover data
    serial.write(command.encode() + b'\r')

    # Read echoed command
    echo = serial.read_until(b'\r')
    # Read actual response
    response = serial.read_until(b'\r')

    return response.decode().strip()


def main():
    s = serial.Serial(port="/dev/ttyUSB0", baudrate=19200, bytesize=8, parity="N", timeout=1)

    fg = jds6600.JDS6600(port="/dev/ttyUSB1")
    fg.connect()
    fg.set_frequency(channel=2, value=5000)

    min_freq = 1000
    max_freq = 10000
    step = 100

    last_aset_freq = max_freq
    last_period = 1 / last_aset_freq
    threshold = 0.4

    freq = []
    ampl = []

    fg.set_frequency(channel=2, value=max_freq)
    send_query(s, "aset")
    time.sleep(5)

    for i in range(max_freq, min_freq, -step):
        fg.set_frequency(channel=2, value=i)

        time.sleep(0.5)
        f = get_freq(s)
        freq.append(f)
        a = get_ampl(s)
        ampl.append(a)

        current_period = 1.0 / f
        period_change = abs(current_period - last_period) / last_period

        if period_change >= threshold:
            send_query(s, "aset")
            time.sleep(5)
            last_period = current_period  # update reference

    plt.plot(freq, ampl)
    plt.ylim(ymin=0)
    plt.ylabel("ampl")
    plt.xlabel("freq")

    plt.show()


if __name__ == "__main__":
    main()
