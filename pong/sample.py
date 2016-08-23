
import time
import random
import serial


class RGB(object):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def __unicode__(self):
        return b'{}{}{}'.format(
            chr(self.r),
            chr(self.g),
            chr(self.b)
        )

    def __str__(self):
        return self.__unicode__()


def send(pixels):
    if ser:
        if ser.in_waiting:
            in_data = ser.read(ser.in_waiting)
            print("SERIAL:", in_data)

        for (i, line) in enumerate(pixels):
            out_data = b'GO{}{}'.format(chr(i), ''.join(map(str, line)))
            print('sending', out_data)
            ser.write(out_data)
            print('done sending.')

            if ser.in_waiting:
                in_data = ser.read(ser.in_waiting)
                print("SERIAL:", in_data)


def draw():
    pixels = [[
        RGB(
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        ) for i in range(17)]
        for x in range(11)]

    send(pixels)

ser = None
try:
    acm = raw_input('Which ACM in /dev ? ')
    ser = serial.Serial('/dev/ttyACM' + acm, 9600)

    while True:
        draw()
        time.sleep(0.1)


except:
    print("ERROR: NO SERIAL")
