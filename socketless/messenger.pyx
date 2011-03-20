# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

__all__ = ['Messenger']

from syncless.best_stackless import stackless
from syncless import coio
from syncless.util import Queue
from collections import deque

import socket
import logging
from channel cimport Channel
from channel import Channel, DisconnectedException

cpdef send_all(message, messengers, collector):
    for token, messenger in messengers:
        (<Messenger>messenger).send(message, token, collector)

cpdef invoke_all(message, messengers):
    cdef object messenger
    cdef object token
    collector = Collector(len(messengers))
    for token, messenger in messengers:
        (<Messenger>messenger).send(message, token, collector)
    return collector.collect()

cdef class Collector:
    def __init__(self, unsigned int wait_amount):
        self.wait_queue = Queue()
        self.items = range(wait_amount)
        self.wait_amount = wait_amount

    cpdef collect(self):
        self.wait_queue.popleft()
        return self.items

    def __call__(self, value, token):
        self.items[self.item_count] = (value, token)
        self.item_count += 1
        if self.item_count == self.wait_amount:
            self.wait_queue.append(True)

cdef class Messenger:
    def __init__(self, listener, handshake=None, reconnect_max_interval=15):
        super(Messenger, self).__init__()
        self.reconnect_max_interval = reconnect_max_interval
        self.listener = listener
        self.channel = None
        self.callbacks = None
        self.send_queue = None
        self.sender = None
        self.receiver = None
        self.connector = coio.stackless.tasklet(self._connect)()
        self.disconnected = Queue()
        self.connected = False
        self.handshake = handshake

    def _connect(self):
        min_interval = 0.5
        while True:
            interval = min_interval
            self.disconnected.pop()
            while not self.channel:
                if self.connect():
                    interval = min_interval
                else:
                    coio.sleep(interval)
                    interval = min(interval * 2, self.reconnect_max_interval)

    cpdef connect(self):
        try:
            c = Channel()
            c.connect(self.listener)
            if self.handshake:
                logging.debug('Handshaking: %s', self.handshake)
                challenge, expected_response = self.handshake
                logging.debug('Sending challenge: "%s"', challenge)
                c.send(challenge)
                c.flush()
                logging.debug('Awaiting response')
                response = c.recv()
                logging.debug('Got response: "%s"', response)
                if not response == expected_response:
                    logging.warning('Failed handshake. Expected response "%s" to challenge "%s". Actual response: "%s".', expected_response, challenge, response)
                    return False
                else:
                    logging.debug('Successfully completed handshake.')
            self.channel = c
            self.callbacks = deque()
            self.send_queue = Queue()
            self.sender = stackless.tasklet(self.__send)()
            self.receiver = stackless.tasklet(self._recv)()
            self.connected = True
            return True
        except socket.error, e:
            self._handle_disconnection(e)
            return False
        except DisconnectedException, e:
            self._handle_disconnection(e)
            return False

    def _handle_disconnection(self, e):
        """docstring for handle_error"""
        logging.debug(e)
        self._teardown()
        self.disconnected.append(True)

    def _teardown(self):
        self.connected = False
        if self.sender and self.sender != coio.stackless.getcurrent():
            self.sender.kill()
            self.sender = None
        if self.receiver and self.receiver != coio.stackless.getcurrent():
            self.receiver.kill()
            self.receiver = None
        if self.channel:
            try:
                self.channel.close()
            except DisconnectedException:
                pass
            self.channel = None
        if self.callbacks:
            for token, callback in self.callbacks:
                callback(None, token)
        self.send_queue = None
        self.callbacks = None

    def __send(self):
        while True:
            try:
                while True:
                    message = self.send_queue.popleft()
                    self.channel.send(message)
                    if len(self.send_queue) == 0:
                        break
                self.channel.flush()
            except DisconnectedException, e:
                self._handle_disconnection(e)
                return

    def _recv(self):
        while True:
            try:
                message = self.channel.recv()
                token, callback = self.callbacks.popleft()
                callback(message, token)
            except DisconnectedException, e:
                self._handle_disconnection(e)
                return

    cpdef send(self, message, token, callback):
        if self.connected:
            self.send_queue.append(message)
            self.callbacks.append((token, callback))
        else:
            callback(None, token)

    cpdef close(self):
        if self.connector:
            self.connector.kill()
            self.connector = None
        self._teardown()

    def __repr__(self):
        return 'Messenger(%s:%d)' % self.listener
