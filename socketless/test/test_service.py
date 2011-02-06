# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
import sys
import os
import time
import gc
from subprocess import Popen

from syncless import coio
import paths
import unittest

from utils.testcase import TestCase

from socketless.service import Protocol, Service, ServiceServer, Method, ServiceClient, MultiServiceClient
from socketless.messenger import Collector

class StoreProtocol(Protocol):
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

    def set(self, callback, key, value):
        self.data[key] = value
        callback(None)

    def get(self, callback, key):
        callback(self.data.get(key, None))

def spawn_server(port):
    return Popen('python %s %d' % (os.path.abspath(__file__), port), shell=True)

class ServiceTest(TestCase):
    def setUp(self):
        self.clients = []
        self.servers = []
        super(ServiceTest, self).setUp()

    def tearDown(self):
        for server in self.servers:
            server.stop()
        for client in self.clients:
            client.close()
        coio.stackless.schedule()
        super(ServiceTest, self).tearDown()

    def testInProcessSingleService(self):
        print
        print 'testInProcessSingleService'
        N = 1000
        listener = ('localhost', 6000)
        server = ServiceServer(listener, [StoreService()])
        server.serve()
        self.servers.append(server)
        store_client = ServiceClient(listener, StoreProtocol())
        self.clients.append(store_client)
        coio.stackless.schedule()
        start = time.time()
        for i in xrange(N):
            key = 'foo%d' % i
            value = 'bar%d' % i
            store_client.set(key, value)
            assert store_client.get(key) == value
        elapsed = time.time() - start
        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInProcessSingleService_Async(self):
         print
         print 'testInProcessSingleService_Async'
         N = 1000
         listener = ('localhost', 6000)
         server = ServiceServer(listener, [StoreService()])
         server.serve()
         self.servers.append(server)
         store_client = ServiceClient(listener, StoreProtocol())
         self.clients.append(store_client)
         while not store_client.is_connected():
             coio.sleep(0.01)

         data = [('foo%d' % i, 'bar%d' % i) for i in xrange(N)]
         data = [(key, value) for key, value in data]
         start = time.time()

         collector = store_client.set_collector(N)
         for key, value in data:
             store_client.set_async(collector, key, value)
         replies = collector.collect()
         assert len(replies) == len(data)

         collector = store_client.get_collector(N)
         for key, value in data:
             store_client.get_async(collector, key)
         replies = collector.collect()
         elapsed = time.time() - start

         assert len(replies) == len(data)
         for (fetched_value, client), (key, value) in zip(replies, data):
             if fetched_value != value:
                 print '%s (%d %s) != %s (%d %s)' % (repr(fetched_value), len(fetched_value), type(fetched_value), repr(value), len(value), type(value))
             assert fetched_value == value

         print 'Elapsed: %.2fs' % elapsed
         print '%.2f invocations / s' % (2 * N / elapsed)

    def testInProcessMultiService(self):
        print
        print 'testInProcessMultiService'
        N = 1000
        listener1 = ('localhost', 6000)
        listener2 = ('localhost', 6001)
        server1 = ServiceServer(listener1, [StoreService()])
        server2 = ServiceServer(listener2, [StoreService()])
        self.servers.append(server1)
        self.servers.append(server2)
        server1.serve()
        server2.serve()
        listeners = [listener1, listener2]
        clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]
        self.clients.extend(clients)
        store_client = MultiServiceClient(clients, StoreProtocol())
        coio.stackless.schedule()
        start = time.time()
        for i in xrange(N):
            key = 'foo%d' % i
            value = 'bar%d' % i
            store_client.set(key, value)
            values = store_client.get(key)
            for token, received_value in values:
                assert str(received_value) == str(value)
        elapsed = time.time() - start
        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (len(listeners) * N / elapsed)

    def testInterProcessSingleService(self):
        print
        print 'testInterProcessSingleService'
        N = 1000
        self.registerSubprocess(spawn_server(6000))
        listener = ('localhost', 6000)
        store_client = ServiceClient(listener, StoreProtocol())
        self.clients.append(store_client)
        while not store_client.is_connected():
            coio.sleep(0.01)
        start = time.time()
        for i in xrange(N):
            key = 'foo%d' % i
            value = 'bar%d' % i
            store_client.set(key, value)
            assert store_client.get(key) == value
        elapsed = time.time() - start
        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInterProcessSingleService_Async(self):
        print
        print 'testInterProcessSingleService_Async'
        N = 10000
        self.registerSubprocess(spawn_server(6000))
        listener = ('localhost', 6000)
        store_client = ServiceClient(listener, StoreProtocol())
        self.clients.append(store_client)
        while not store_client.is_connected():
            coio.sleep(0.01)

        data = [('foo%d' % i, 'bar%d' % i) for i in xrange(N)]
        data = [(key*100, value*100) for key, value in data]
        start = time.time()

        collector = store_client.set_collector(N)
        for key, value in data:
            store_client.set_async(collector, key, value)
        replies = collector.collect()
        assert len(replies) == len(data)

        collector = store_client.get_collector(N)
        for key, value in data:
            store_client.get_async(collector, key)
        replies = collector.collect()
        assert len(replies) == len(data)

        elapsed = time.time() - start

        for (fetched_value, client), (key, value) in zip(replies, data):
            if fetched_value != value:
                print '%s (%d %s) != %s (%d %s)' % (repr(fetched_value), len(fetched_value), type(fetched_value), repr(value), len(value), type(value))
            assert fetched_value == value

        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (2 * N / elapsed)

    def testInterProcessMultiService(self):
        print
        print 'testInterProcessMultiService'
        N = 100
        ports = range(6000, 6010)
        for port in ports:
            self.registerSubprocess(spawn_server(port))
        listeners = [('localhost', port) for port in ports]
        clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]
        self.clients.extend(clients)

        store_client = MultiServiceClient(clients, StoreProtocol())
        while not store_client.is_connected():
            coio.sleep(0.1)

        start = time.time()
        for i in xrange(N):
            key = 'foo%d' % i
            value = 'bar%d' % i
            store_client.set(key, value)
            values = store_client.get(key)
            for token, received_value in values:
                if str(received_value) != str(value):
                    print received_value, value
                assert str(received_value) == str(value)
        elapsed = time.time() - start
        print 'Elapsed: %.2fs' % elapsed
        print '%.2f invocations / s' % (len(ports) * N / elapsed)


    def testInterProcessMultiService_Async(self):
        print
        print 'testInterProcessMultiService_Async'
        M = 10
        N = 100
        ports = range(6000, 6000 + M)
        for port in ports:
            self.registerSubprocess(spawn_server(port))
        listeners = [('localhost', port) for port in ports]
        clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]
        self.clients.extend(clients)
        store_client = MultiServiceClient(clients, StoreProtocol())

        keys = ['foo%d' % i for i in xrange(N)]
        values = ['bar%d' % i for i in xrange(N)]

        while not store_client.is_connected():
            coio.sleep(0.1)

        start = time.time()

        collector = store_client.set_collector(N)
        for key, value in zip(keys, values):
            store_client.set_async(collector, key, value)
        collector.collect()

        collector = store_client.get_collector(N)
        for key in keys:
            store_client.get_async(collector, key)
        received_value_lists = collector.collect()

        elapsed = time.time() - start
        for token, received_values in received_value_lists.iteritems():
            for value, received_value in zip(values, received_values):
                if str(received_value) != str(value):
                    print received_value, value
                assert str(received_value) == str(value)

        invocation_count = 2 * len(ports) * N
        print 'Elapsed: %.2fs' % elapsed
        print 'Invocations: %d' % invocation_count
        print '%.2f invocations / s' % (invocation_count / elapsed)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        listener = ('localhost', port)
        server = ServiceServer(listener, [StoreService()])
        server.serve()
        while True:
            coio.sleep(1)
    else:
        unittest.main()
