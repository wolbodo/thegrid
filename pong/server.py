
import os
import json
import time
from datetime import timedelta

import tornado.ioloop
import tornado.web
import tornado.websocket

import serial

static_root = os.path.join(os.path.dirname(__file__), 'static')


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


ser = None
try:
    acm = raw_input('Which ACM in /dev ? ')
    ser = serial.Serial('/dev/ttyACM' + acm, 9600)

    pixels = [[RGB(220, 220, 50)] * 17] * 11

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

    time.sleep(1)
    pixels = [[RGB(0, 220, 200)] * 17] * 11

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


except:
    print("ERROR: NO SERIAL")


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class Game(object):

    def __init__(self, *players):
        self.background = RGB(120, 20, 50)
        print('constructing game')
        self.players = players
        self.timers = []
        self.ball = (8, 5)

        self.start_game()

    def draw(self):
        self.background.g = (self.background.g + 5) % 255
        # Draw background
        pixels = [[self.background] * 17 for i in range(11)]

        # Draw positions (boards)
        player1 = self.players[0]
        player2 = self.players[1]

        for y in range(
            player1.position - 2,
            player1.position + 2,
        ):
            if y < 0:
                y = 0
            elif y > 10:
                y == 10
            pixels[y][0] = RGB(50, 255, 0)
            pixels[y][1] = RGB(50, 255, 0)

        for y in range(
            player2.position - 2,
            player2.position + 2,
        ):
            if y < 0:
                y = 0
            elif y > 10:
                y == 10
            pixels[y][15] = RGB(50, 0, 255)
            pixels[y][16] = RGB(50, 0, 255)

        # Draw ball
        for x in range(self.ball[0] - 1, self.ball[0] + 1):
            for y in range(self.ball[1] - 1, self.ball[1] + 1):
                pixels[y][x] = RGB(255, 255, 255)

        if ser:
            print('starting to send data')
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

        ioloop.add_timeout(
            timedelta(seconds=1),
            self.draw
        )

    def send_later(self, msg):
        def later():
            print("sending", msg)
            for player in self.players:
                player.write_message(msg)
        return later

    def start_game(self):
        print('starting game')
        self.ended = False

        self.draw()

        self.timers.extend([
            ioloop.add_timeout(
                timedelta(seconds=1),
                self.send_later('starting game in 3...')
            ),
            ioloop.add_timeout(
                timedelta(seconds=2),
                self.send_later('starting game in 2...')
            ),
            ioloop.add_timeout(
                timedelta(seconds=3),
                self.send_later('starting game in 1...')
            ),
            ioloop.add_timeout(
                timedelta(seconds=4),
                self.send_later('GOGOGOGOGO...')
            ),
            ioloop.add_timeout(
                timedelta(seconds=4),
                self.end_game
            )
        ])

    def end_game(self):
        self.ended = True

    def stop(self):
        print("Stopping game forced")
        self.end_game()

        while self.timers:
            ioloop.remove_timeout(self.timers.pop())

    def contains(self, player):
        print("Checking for players")
        if player in self.players:
            print('player in this game')
            return True
        return False


class PongHandler(tornado.websocket.WebSocketHandler):

    active_game = None
    queue = []

    def __init__(self, *args, **kwargs):
        super(PongHandler, self).__init__(*args, **kwargs)

        self.position = 0

    @staticmethod
    def join_queue(handler):
        PongHandler.queue.append(handler)

        handler.write_message(json.dumps({
            'queue_position': PongHandler.queue.index(handler),
            'active_game': bool(PongHandler.active_game)
        }))

    @staticmethod
    def leave_queue(handler):
        print("Leaving queue")
        if handler in PongHandler.queue:
            print("from queue")
            PongHandler.queue.remove(handler)
        elif (PongHandler.active_game and
                PongHandler.active_game.contains(handler)):
            print("from game")
            # Stop current game
            PongHandler.active_game.stop()

    @staticmethod
    def try_start_game():
        active_game = PongHandler.active_game

        print('trying to start game: queue: {}, game: {}'.format(
            len(PongHandler.queue),
            active_game and not active_game.ended
        ))
        if (
            (len(PongHandler.queue) >= 2) and
            not (active_game and not active_game.ended)
        ):
            print("Starting game")
            # ready to start the game
            PongHandler.active_game = Game(
                PongHandler.queue.pop(0),
                PongHandler.queue.pop(0),
            )

    def open(self):
        PongHandler.join_queue(self)
        PongHandler.try_start_game()

    def on_message(self, message):
        print('Received', message)
        try:
            data = json.loads(message)
            if 'position' in data:
                self.position = int(data.get('position'))
        except:
            pass

    def on_close(self):
        PongHandler.leave_queue(self)

        print("WebSocket closed")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/socket", PongHandler),
        (r'/(.*)', tornado.web.StaticFileHandler, {'path': static_root}),
    ],
        debug=True,
        static_path=static_root,
        template_path=static_root
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    ioloop = tornado.ioloop.IOLoop.current()

    try:
        ioloop.start()
    except KeyboardInterrupt:
        if ser:
            ser.close()
