
import os
import json
from datetime import timedelta

import tornado.ioloop
import tornado.web
import tornado.websocket

import serial

static_root = os.path.join(os.path.dirname(__file__), 'static')

try:
    ser = serial.Serial('/dev/ttyACM0', 9600)
except:
    print("ERROR: NO SERIAL")


def rgb(r, g, b):
    return '{}{}{}'.format(chr(r), chr(g), chr(b))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class Game(object):

    def __init__(self, *players):
        self.players = players
        self.timers = []

        self.start_game()

    def send_later(self, msg):
        def later():
            print("sending", msg)
            for player in self.players:
                player.write_message(msg)
        return later

    def start_game(self):
        self.ended = False

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
        elif PongHandler.active_game.contains(handler):
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
        self.write_message(u"You said: " + message)

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
    ioloop.start()
