import serial
from typing import Type
from enum import Enum
import time


class LedCommands(Enum):
    SET_LED = 1
    RENDER = 2
    RESET = 3
    SET_BRIGHTNESS = 4


class ColorException(Exception):
    def __init__(self, message):
        self.message = message

class BrightnessException(Exception):
    def __init__(self, message):
        self.message = message


class Color:
    def __init__(self, white: int, red: int, green: int, blue: int):
        self.white = white
        self.red = red
        self.green = green
        self.blue = blue

    def _validate_color(self, value: int):
        if value < 0 or value > 255:
            raise ColorException(
                "Value {} is out of range".format(value)
            )

    @property
    def white(self):
        return self._white

    @white.setter
    def white(self, value: int):
        self._validate_color(value)
        self._white = value

    @property
    def red(self):
        return self._red

    @red.setter
    def red(self, value: int):
        self._validate_color(value)
        self._red = value

    @property
    def green(self):
        return self._green

    @green.setter
    def green(self, value: int):
        self._validate_color(value)
        self._green = value

    @property
    def blue(self):
        return self._blue

    @blue.setter
    def blue(self, value: int):
        self._validate_color(value)
        self._blue = value


class HSVColor:
    def __init__(self, hue: int, saturation: int = 255, brightness: int = 255):
        self._hue = hue
        self._saturation = saturation
        self._brightness = brightness
        self._white = 0
        self._red = 0
        self._green = 0
        self._blue = 0
        self._calcuate_rgb()

    def _calcuate_rgb(self):
        red = 0
        green = 0
        blue = 0
        hue = ((self._hue * 1530 + 32768) // 65536) % 1530

        if hue < 510:
            blue = 0
            if hue < 255:
                red = 255
                green = hue
            else:
                red = 510 - hue
                green = 255
        elif hue < 1020:
            red = 0
            if hue < 765:
                green = 255
                blue = hue - 510
            else:
                green = 1020 - hue
                blue = 255
        elif hue < 1530:
            green = 0
            if hue < 1275:
                red = hue - 1020
                blue = 255
            else:
                red = 255
                blue = 1530 - hue
        else:
            red = 255
            green = blue = 0

        brightness = self._brightness + 1
        saturation1 = self._saturation + 1
        saturation2 = 255 - self._saturation

        self._red = ((((red * saturation1) >> 8) +
                      saturation2) * brightness) >> 8
        self._green = ((((green * saturation1) >> 8) +
                        saturation2) * brightness) >> 8
        self._blue = ((((blue * saturation1) >> 8) +
                       saturation2) * brightness) >> 8

    def to_color(self):
        return Color(0, self._red, self._green, self._blue)


class GammaColor:
    gamma_table = [
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
        0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  1,  1,  1,
        1,  1,  1,  1,  2,  2,  2,  2,  2,  2,  2,  2,  3,  3,  3,  3,
        3,  3,  4,  4,  4,  4,  5,  5,  5,  5,  5,  6,  6,  6,  6,  7,
        7,  7,  8,  8,  8,  9,  9,  9, 10, 10, 10, 11, 11, 11, 12, 12,
        13, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20,
        20, 21, 21, 22, 22, 23, 24, 24, 25, 25, 26, 27, 27, 28, 29, 29,
        30, 31, 31, 32, 33, 34, 34, 35, 36, 37, 38, 38, 39, 40, 41, 42,
        42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57,
        58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 69, 70, 71, 72, 73, 75,
        76, 77, 78, 80, 81, 82, 84, 85, 86, 88, 89, 90, 92, 93, 94, 96,
        97, 99, 100, 102, 103, 105, 106, 108, 109, 111, 112, 114, 115, 117, 119, 120,
        122, 124, 125, 127, 129, 130, 132, 134, 136, 137, 139, 141, 143, 145, 146, 148,
        150, 152, 154, 156, 158, 160, 162, 164, 166, 168, 170, 172, 174, 176, 178, 180,
        182, 184, 186, 188, 191, 193, 195, 197, 199, 202, 204, 206, 209, 211, 213, 215,
        218, 220, 223, 225, 227, 230, 232, 235, 237, 240, 242, 245, 247, 250, 252, 255
    ]

    def __init__(self, color: Type[Color]):
        self._white = GammaColor.gamma_table[color.white]
        self._red = GammaColor.gamma_table[color.red]
        self._green = GammaColor.gamma_table[color.green]
        self._blue = GammaColor.gamma_table[color.blue]

    def to_color(self):
        return Color(self._white, self._red, self._green, self._blue)
        


class LedDriver:

    def __init__(self, port: str, baudrate: int = 115200, timeout: int = 1, num_leds: int = 300):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._num_leds = num_leds
        self._serial_conn = serial.Serial(
            self._port,
            self._baudrate,
            timeout=self._timeout,
        )

    def __del__(self):
        self._serial_conn.close()

    def reset(self):
        message = bytes([
            LedCommands.RESET.value,
            0, 0, 0, 0, 0, 0
        ])
        self._serial_conn.write(message)

    def set_led(self, index: int, color: Type[Color]):
        message = bytes([
            LedCommands.SET_LED.value,
            *index.to_bytes(2, "big"),
            color.white,
            color.red,
            color.green,
            color.blue
        ])
        self._serial_conn.write(message)

    def set_brightness(self, brightness: int):
        if brightness < 0 or brightness > 255:
            raise BrightnessException("{} is an invalid brightness".format(brightness))
        message = bytes([
            LedCommands.SET_BRIGHTNESS.value,
            brightness,
            0, 0, 0, 0, 0
        ])
        self._serial_conn.write(message)

    def render(self):
        message = bytes([
            LedCommands.RENDER.value,
            0, 0, 0, 0, 0, 0
        ])
        self._serial_conn.write(message)



def rainbow(driver: Type[LedDriver], wait: int = 10):
    for first_pixe_hue in range(0, 5*65536, 256):
        for led_index in range(300):
            led_hue = first_pixe_hue + (led_index * 65536 // 300)
            driver.set_led(led_index, HSVColor(led_hue).to_color())
        driver.render()
        time.sleep(wait / 1000)

def theaterChase(driver: Type[LedDriver], color: Type[Color],  wait: int = 50):
    for _ in range(10):
        for j in range(3):
            driver.reset()
            for k in range(j, 300, 3):
                driver.set_led(k, color)
            driver.render()
            time.sleep(wait / 1000)

def glow(driver: Type[LedDriver], wait: int = 180):
    colors = [
        Color(0, 0, 0, 0),Color(0, 50, 0, 0), Color(0, 100, 0, 0), Color(0, 150, 0, 0), Color(0, 200, 0, 0), Color(0, 250, 0, 0),
        Color(0, 0, 0, 0),Color(0, 0, 50, 0), Color(0, 0, 100, 0), Color(0, 0, 150, 0), Color(0, 0, 200, 0), Color(0, 0, 250, 0),
        Color(0, 0, 0, 0),Color(0, 0, 0, 50), Color(0, 0, 0, 100), Color(0, 0, 0, 150), Color(0, 0, 0, 200), Color(0, 0, 0, 250)
    ]
    for color in colors:
        for i in range(300):
            driver.set_led(i, color)
        driver.render()
        time.sleep(wait / 1000)


def theaterChaseRainbow(driver: Type[LedDriver], wait: int = 50):
    first_led_hue = 0
    for _ in range(30):
        for j in range(3):
            driver.reset()
            for k in range(j, 300, 3):
                hue = first_led_hue + k * 65536 // 300
                color = GammaColor(HSVColor(hue).to_color()).to_color()
                driver.set_led(k, color)
            driver.render()
            time.sleep(wait / 1000)
            first_led_hue += 65536 // 90

def snake(driver: Type[LedDriver], wait: int = 50):
    snake_size = 10

    for i in range(0, 300 - snake_size, 1):
        driver.reset()
        for j in range(snake_size):
            driver.set_led(i + j, Color(0, 138,7,7))
        driver.render()
        time.sleep(wait / 1000)
    
    for i in range(300 - snake_size, 0, -1):
        driver.reset()
        for j in range(snake_size):
            driver.set_led(i + j,  Color(0, 138,7,7))
        driver.render()
        time.sleep(wait / 1000)


def ocean(driver: Type[LedDriver], wait: int = 50):
    last_pixel_pos = 299
    last_pixel_incr = -1
    first_pixel_position = 0
    first_pixel_incr = 1

    while True:
        driver.reset()
        driver.set_led(first_pixel_position, Color(0, 255, 0, 0))
        driver.set_led(last_pixel_pos, Color(0, 0, 0, 255))
        driver.render()

        first_pixel_position += first_pixel_incr
        last_pixel_pos += last_pixel_incr

        if last_pixel_pos == 0 or last_pixel_pos == 300:
            last_pixel_incr *= -1
        
        if first_pixel_position == 0 or first_pixel_position == 300:
            first_pixel_incr *= -1



def main():
    driver = LedDriver("COM5")
    driver.reset()
    driver.set_brightness(64)

    ocean(driver)
        
        




if __name__ == "__main__":
    main()
