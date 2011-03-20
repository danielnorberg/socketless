# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
import sys
import os
import time
from subprocess import Popen

import paths
paths.setup()

from syncless import coio
import unittest

from utils.testcase import TestCase
from utils import debug

from socketless.service import Method, Protocol, Service, Server, Client, MulticastClient
from socketless.messenger import Collector

class StoreProtocol(Protocol):
    handshake = ('Store', 'Ok')
    methods = dict(
        set = Method('s', [('key', str), ('timestamp', long), ('value', str)], [('timestamp', long)]),
        get = Method('g', [('key', str)], [('timestamp', long), ('value', str)]),
    )

class StoreService(Service):
    def __init__(self):
        super(StoreService, self).__init__(StoreProtocol(),
            set = self.set,
            get = self.get,
        )
        self.data = {}

    def set(self, key, timestamp, value):
        self.data[key] = (timestamp, value)
        return timestamp

    def get(self, key):
        timestamp, value = self.data.get(key, (None, None))
        return timestamp or 0, value

def spawn_server(port):
    return Popen('%s %s %d' % (sys.executable, os.path.abspath(__file__), port), shell=True)

class ServiceTest(TestCase):
    def setUp(self):
        self.clients = []
        self.servers = []
        super(ServiceTest, self).setUp()

    def tearDown(self):
        for server in self.servers:
            server.stop()
        for client in self.clients:
            client.disconnect()
        coio.stackless.schedule()
        super(ServiceTest, self).tearDown()

    def testInProcessSingleService_Sync(self):
        print
        print 'testInProcessSingleService_Sync'
        N = 1000
        listener = ('localhost', 16000)
        server = Server(listener, [StoreService()])
        server.serve()
        self.servers.append(server)
        store_client = Client(listener, StoreProtocol())
        store_client.connect()
        self.clients.append(store_client)
        while not store_client.is_connected():
            coio.sleep(0.01)
        coio.stackless.schedule()

        values = [('foo%d' % i, i, 'bar%d' % i) for i in xrange(N)]
        received_values = []

        start = time.time()
        for key, timestamp, value in values:
            retreived_timestamp = store_client.set(key, timestamp, value)
            assert retreived_timestamp == timestamp
            received_values.append(store_client.get(key))
        elapsed = time.time() - start

        for (key, timestamp, value), (received_timestamp, received_value) in zip(values, received_values):
            assert timestamp == received_timestamp
            assert value == received_value

        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInProcessSingleService_Async(self):
        print
        print 'testInProcessSingleService_Async'
        N = 1000
        listener = ('localhost', 16100)
        server = Server(listener, [StoreService()])
        server.serve()
        self.servers.append(server)
        store_client = Client(listener, StoreProtocol())
        store_client.connect()
        self.clients.append(store_client)
        while not store_client.is_connected():
            coio.sleep(0.01)

        data = [('foo%d' % i, long(i), 'bar%d' % i) for i in xrange(N)]

        start = time.time()

        collector = store_client.set_collector(N)
        for key, timestamp, value in data:
            store_client.set_async(collector, key, timestamp, value)
        replies = collector.collect()
        assert len(replies) == len(data)

        collector = store_client.get_collector(N)
        for key, timestamp, value in data:
            store_client.get_async(collector, key)
        replies = collector.collect()

        elapsed = time.time() - start

        assert len(replies) == len(data)
        for ((fetched_timestamp, fetched_value), client), (key, timestamp, value) in zip(replies, data):
            if fetched_value != value:
                print '%s (%d %s) != %s (%d %s)' % (repr(fetched_value), len(fetched_value), type(fetched_value), repr(value), len(value), type(value))
            assert fetched_value == value
            assert fetched_timestamp == timestamp

        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInProcessMultiService_Sync(self):
        print
        print 'testInProcessMultiService_Sync'
        N = 1000
        listener1 = ('localhost', 16200)
        listener2 = ('localhost', 16201)
        server1 = Server(listener1, [StoreService()])
        server2 = Server(listener2, [StoreService()])
        self.servers.append(server1)
        self.servers.append(server2)
        server1.serve()
        server2.serve()
        listeners = [listener1, listener2]
        clients = [Client(listener, StoreProtocol()) for listener in listeners]
        for client in clients:
            client.connect()
            while not client.is_connected():
                coio.sleep(0.01)
        self.clients.extend(clients)
        store_client = MulticastClient(StoreProtocol())
        coio.stackless.schedule()

        values = [('foo%d' % i, i, 'bar%d' % i) for i in xrange(N)]
        received_values_list = []

        start = time.time()

        for key, timestamp, value in values:
            store_client.set(clients, key, timestamp, value)
            received_values_list.append(store_client.get(clients, key))

        elapsed = time.time() - start

        for received_values, (key, timestamp, value) in zip(received_values_list, values):
            for token, (received_timestamp, received_value) in received_values:
                if str(received_value) != str(value):
                    print received_value, value
                assert str(received_value) == str(value)
                assert received_timestamp == timestamp

        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (len(listeners) * 2 * N / elapsed)

    def testInterProcessSingleService(self):
        print
        print 'testInterProcessSingleService'
        N = 1000
        self.registerSubprocess(spawn_server(16300))
        listener = ('localhost', 16300)
        store_client = Client(listener, StoreProtocol())
        store_client.connect()
        self.clients.append(store_client)
        while not store_client.is_connected():
            coio.sleep(0.01)
        values = [('foo%d' % i, i, 'bar%d' % i) for i in xrange(N)]
        received_values = []
        start = time.time()
        for key, timestamp, value in values:
            store_client.set(key, timestamp, value)
            received_values.append(store_client.get(key))
        elapsed = time.time() - start
        for (key, timestamp, value), (received_timestamp, received_value) in zip(values, received_values):
            assert timestamp == received_timestamp
            assert value == received_value
        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInterProcessSingleService_Async(self):
        print
        print 'testInterProcessSingleService_Async'
        N = 100000
        self.registerSubprocess(spawn_server(16400))
        listener = ('localhost', 16400)
        store_client = Client(listener, StoreProtocol())
        store_client.connect()
        self.clients.append(store_client)
        while not store_client.is_connected():
            coio.sleep(0.01)

        data = [('foo%d' % i, i, 'bar%d' % i) for i in xrange(N)]
        data = [(key*100, timestamp, value*100) for key, timestamp, value in data]

        start = time.time()

        collector = store_client.set_collector(N)
        for key, timestamp, value in data:
            store_client.set_async(collector, key, timestamp, value)
        replies = collector.collect()
        assert len(replies) == len(data)

        collector = store_client.get_collector(N)
        for key, timestamp, value in data:
            store_client.get_async(collector, key)
        replies = collector.collect()
        assert len(replies) == len(data)

        elapsed = time.time() - start

        for ((fetched_timestamp, fetched_value), client), (key, timestamp, value) in zip(replies, data):
            if fetched_value != value:
                print '%s (%d %s) != %s (%d %s)' % (repr(fetched_value), len(fetched_value), type(fetched_value), repr(value), len(value), type(value))
            assert fetched_value == value
            assert fetched_timestamp == timestamp

        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInterProcessMultiService_Sync(self):
        print
        print 'testInterProcessMultiService_Sync'
        N = 1000
        ports = range(16500, 16510)
        for port in ports:
            self.registerSubprocess(spawn_server(port))
        listeners = [('localhost', port) for port in ports]
        clients = [Client(listener, StoreProtocol()) for listener in listeners]
        self.clients.extend(clients)
        for client in clients:
            client.connect()
            while not client.is_connected():
                coio.sleep(0.1)

        store_client = MulticastClient(StoreProtocol())

        values = [('foo%d' % i, i, 'bar%d' % i) for i in xrange(N)]

        received_values_list = []
        start = time.time()
        for key, timestamp, value in values:
            store_client.set(clients, key, timestamp, value)
            received_values = store_client.get(clients, key)
            received_values_list.append(received_values)
        elapsed = time.time() - start

        for received_values, (key, timestamp, value) in zip(received_values_list, values):
            for token, (received_timestamp, received_value) in received_values:
                if str(received_value) != str(value):
                    print received_value, value
                assert str(received_value) == str(value)
                assert received_timestamp == timestamp

        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (len(ports) * N / elapsed)


    def testInterProcessMultiService_Async(self):
        print
        print 'testInterProcessMultiService_Async'
        M = 10
        N = 1000
        ports = range(16600, 16600 + M)
        for port in ports:
            self.registerSubprocess(spawn_server(port))
        listeners = [('localhost', port) for port in ports]
        clients = [Client(listener, StoreProtocol()) for listener in listeners]
        self.clients.extend(clients)
        for client in clients:
            client.connect()
            while not client.is_connected():
                coio.sleep(0.1)

        store_client = MulticastClient(StoreProtocol())

        keys = ['foo%d' % i for i in xrange(N)]
        timestamps = [i for i in xrange(N)]
        values = ['bar%d' % i for i in xrange(N)]

        start = time.time()

        collector = store_client.set_collector(clients, N)
        for key, timestamp, value in zip(keys, timestamps, values):
            store_client.set_async(collector, key, timestamp, value)
        collector.collect()

        collector = store_client.get_collector(clients, N)
        for key in keys:
            store_client.get_async(collector, key)
        received_value_lists = collector.collect()

        elapsed = time.time() - start

        for token, received_values in received_value_lists.iteritems():
            for timestamp, value, (received_timestamp, received_value) in zip(timestamps, values, received_values):
                if str(received_value) != str(value):
                    print received_value, value
                assert str(received_value) == str(value)
                assert received_timestamp == timestamp

        invocation_count = 2 * len(ports) * N
        print 'Elapsed: %.2fs' % elapsed
        print 'Invocations: %d' % invocation_count
        print '%.2f invocations / s' % (invocation_count / elapsed)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        listener = ('localhost', port)
        server = Server(listener, [StoreService()])
        server.serve()
        while True:
            coio.sleep(1)
    else:
        unittest.main()
