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
            print '%.2f invocations / s' % (N / elapsed)
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
        p = Popen('python %s 6000' % os.path.abspath(__file__), shell=True)
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
            print '%.2f invocations / s' % (N / elapsed)
        finally:
            p.kill()

    def testInterProcessMultiService(self):
        print
        print 'testInterProcessMultiService'
        N = 1000
        ports = range(6000, 6010)
        ps = [Popen('python %s %d' % (os.path.abspath(__file__), port), shell=True) for port in ports]
        listeners = [('localhost', port) for port in ports]
        try:
            clients = [ServiceClient(listener, StoreProtocol()) for listener in listeners]
            store_client = MultiServiceClient(clients, StoreProtocol())
            coio.sleep(1)
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
            print '%.2f invocations / s' % (len(ports) * N / elapsed)
        finally:
            for p in ps:
                p.kill()
            coio.stackless.schedule()


    def testMultiServiceClientUpdateSpeed(self):
        print
        print 'testMultiServiceClientUpdateSpeed'
        N = 100000
        ports = range(6000, 6005)
        listeners = [('localhost', port) for port in ports]
        gc.disable()
        all_clients = []
        try:
            protocol = StoreProtocol()
            clients = [ServiceClient(listener, protocol) for listener in listeners]
            multiservice_client = MultiServiceClient(clients, protocol)
            start = time.time()
            for i in xrange(N):
                multiservice_client.update_clients(clients)
            elapsed = time.time() - start
            print 'Elapsed: %.2fs' % elapsed
            print '%.2f updates / s' % (N / elapsed)
            for client in clients:
                client.close()
        finally:
            gc.enable()

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
