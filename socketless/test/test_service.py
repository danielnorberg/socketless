# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

from syncless import coio
import logging
import paths
import unittest

from utils.testcase import TestCase

from socketless.service import Protocol, Service, ServiceServer, Method, ServiceClient, MultiServiceClient
from socketless.messenger import Messenger, invoke_all

class StoreProtocol(object):
    handshake = ('Store', 'Ok')
    methods = dict(
        set = Method('s', [('key', str), ('value', str)], []),
        get = Method('g', [('key', str)], [('value', str)]),
    )

class StoreService(Service):
    def __init__(self):
        super(StoreService, self).__init__(StoreProtocol(),
            set = self.set,
            get = self.get,
        )
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)

class ServiceTest(TestCase):

    def testSingleService(self):
        listener = ('localhost', 6000)
        server = ServiceServer(listener, [StoreService()])
        server.serve()
        try:
            coio.sleep(0.1)

            store_client = ServiceClient(listener, StoreProtocol())

            for i in xrange(100):
                key = 'foo%d' % i
                value = 'bar%d' % i

                store_client.set(key, value)
                assert store_client.get(key) == value
        finally:
            server.stop()

    def testMultiService(self):
        listener1 = ('localhost', 6000)
        listener2 = ('localhost', 6001)
        server1 = ServiceServer(listener1, [StoreService()])
        server2 = ServiceServer(listener2, [StoreService()])
        server1.serve()
        server2.serve()
        try:
            listeners = [listener1, listener2]
            clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]

            coio.sleep(1.0)

            store_client = MultiServiceClient(clients, StoreProtocol())

            for i in xrange(100):
                key = 'foo%d' % i
                value = 'bar%d' % i

                store_client.set(key, value)
                values = store_client.get(key)
                for token, received_value in values:
                    assert str(received_value) == str(value)

        finally:
            server1.stop()
            server2.stop()


if __name__ == '__main__':
    unittest.main()
