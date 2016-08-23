#!/usr/bin/python

import font
import serial

ser = serial.Serial('/dev/ttyACM0', 9600)


def rgb(r, g, b):
    return '{}{}{}'.format(chr(r), chr(g), chr(b))


def scrollText(text, color):
    buffer = [' ' * 17] * 11


# GO0000000000000000000000000000 17 * 3
# GO1000000000000000000000000000 17 * 3
# GO2000000000000000000000000000 17 * 3
# GO3000000000000000000000000000 17 * 3

if __name__ == '__main__':
    scrollText('HELLO WORLD', rgb(255, 255, 0))
