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

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)

def spawn_server(port):
    return Popen('python %s %d' % (os.path.abspath(__file__), port), shell=True)

class ServiceTest(TestCase):
    def testInProcessSingleService(self):
        print
        print 'testInProcessSingleService'
        N = 1000
        listener = ('localhost', 6000)
        server = ServiceServer(listener, [StoreService()])
        server.serve()
        try:
            store_client = ServiceClient(listener, StoreProtocol())
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
        finally:
            server.stop()

    def testInProcessMultiService(self):
        print
        print 'testInProcessMultiService'
        N = 1000
        listener1 = ('localhost', 6000)
        listener2 = ('localhost', 6001)
        server1 = ServiceServer(listener1, [StoreService()])
        server2 = ServiceServer(listener2, [StoreService()])
        server1.serve()
        server2.serve()
        try:
            listeners = [listener1, listener2]
            clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]
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
        finally:
            server1.stop()
            server2.stop()

    def testInterProcessSingleService(self):
        print
        print 'testInterProcessSingleService'
        N = 1000
        p = spawn_server(6000)
        listener = ('localhost', 6000)
        try:
            store_client = ServiceClient(listener, StoreProtocol())
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
        finally:
            p.kill()

    def testInterProcessSingleService_Async(self):
        print
        print 'testInterProcessSingleService_Async'
        N = 10000
        p = spawn_server(6000)
        listener = ('localhost', 6000)
        try:
            store_client = ServiceClient(listener, StoreProtocol())
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
            for (fetched_value, client), (key, value) in zip(replies, data):
                if fetched_value != value:
                    print '%s (%d %s) != %s (%d %s)' % (repr(fetched_value), len(fetched_value), type(fetched_value), repr(value), len(value), type(value))
                assert fetched_value == value

            elapsed = time.time() - start
            print 'Elapsed: %.2fs' % elapsed
            print '%.2f invocations / s' % (2 * N / elapsed)
        finally:
            p.kill()

    def testInterProcessMultiService(self):
        print
        print 'testInterProcessMultiService'
        N = 1000
        ports = range(6000, 6010)
        ps = [spawn_server(port) for port in ports]
        listeners = [('localhost', port) for port in ports]
        try:
            clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]
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
        finally:
            for p in ps:
                p.kill()
            coio.stackless.schedule()

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
