# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

__all__ = ['ChannelServer']

import socket

from syncless import coio

from channel import Channel

class ChannelServer(object):
    """docstring for ChannelServer"""
    def __init__(self, listener, handle_connection=None, listen_backlog=1024):
        super(ChannelServer, self).__init__()
        self.listening_tasklet = None
        self.listening_socket = None
        self.listen_backlog = listen_backlog
        self.listener = listener
        if handle_connection:
            self.handle_connection = handle_connection

    def serve(self):
        self.listening_tasklet = coio.stackless.tasklet(self._serve)()

    def _serve(self):
        self.listening_socket = coio.nbsocket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listening_socket.bind(self.listener)
        self.listening_socket.listen(self.listen_backlog)
        while True:
            conn, addr = self.listening_socket.accept()
            coio.stackless.tasklet(self.handle_connection)(Channel(conn), addr)
            coio.stackless.schedule()

    def stop(self):
        if self.listening_tasklet:
            self.listening_tasklet.kill()
            self.listening_tasklet = None
        if self.listening_socket:
            self.listening_socket.close()
            self.listening_socket = None

    def serve_forever(self):
        self._serve()
