
import os
import json
import time
import tornado.ioloop
import tornado.web
import tornado.websocket

static_root = os.path.join(os.path.dirname(__file__), 'static')


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class Game(object):

    def __init__(self, *players):
        self.players = players

        self.start_game()

    def start_game(self):
        self.ended = False

        for player in self.players:
            player.write_message('starting game in 3...')

        time.sleep(1)
        for player in self.players:
            player.write_message('2...')

        time.sleep(1)

        for player in self.players:
            player.write_message('1...')

        time.sleep(1)

        for player in self.players:
            player.write_message('GO')

        self.ended = True


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
    def try_start_game():
        active_game = PongHandler.active_game

        print('trying to start game: queue: {}, game: {}'.format(
            len(PongHandler.queue),
            active_game and active_game.ended
        ))
        if (
            (len(PongHandler.queue) >= 2) and
            not (active_game and active_game.ended)
        ):
            print("Starting game")
            # ready to start the game
            active_game = Game(
                PongHandler.queue.pop(0),
                PongHandler.queue.pop(0),
            )

    def open(self):
        PongHandler.join_queue(self)
        PongHandler.try_start_game()

    def on_message(self, message):
        self.write_message(u"You said: " + message)

    def on_close(self):
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
    tornado.ioloop.IOLoop.current().start()
