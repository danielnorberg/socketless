# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

import paths
paths.setup()

from collections import deque
from timeit import default_timer as timer
import os, signal

from syncless import coio
from syncless.util import Queue

from socketless.messenger import Messenger, Collector

from utils.testcase import TestCase
from utils.channel_echoserver import launch_echoserver

class TestMessenger(TestCase):
    def testResilience(self):
        try:
            token = id(self)
            q = Queue()
            def callback(value, token):
                q.append((value, token))
            port = 6000
            host = ('localhost', port)
            p = launch_echoserver(port)
            coio.sleep(1)
            messenger = Messenger(host, reconnect_max_interval=0.1)
            messenger.connect()
            messenger.send('1', token, callback)
            assert q.popleft() == ('1', token)
            os.kill(p.pid, signal.SIGKILL)
            messenger.send('2', token, callback)
            coio.sleep(1)
            messenger.send('3', token, callback)
            assert q.popleft() == (None, token)
            assert q.popleft() == (None, token)
            p = launch_echoserver(port)
            coio.sleep(1)
            messenger.send('4', token, callback)
            assert q.popleft() == ('4', token)
            messenger.close()
            coio.sleep(1)
        finally:
            os.kill(p.pid, signal.SIGKILL)

    def testPerformance(self):
        token = id(self)
        message_length = 1024
        N = 10000
        batch_size = 100
        collector = Collector(batch_size)
        l = 0
        port = 6001
        host = ('localhost', port)
        p = launch_echoserver(port)
        bytecount = 0
        try:
            sent_messages = deque()
            coio.sleep(1)
            messenger = Messenger(host)
            messenger.connect()
            message_buffer = ''.join('%d' % (i % 10) for i in xrange(N+message_length*2))
            i = 0
            start_time = timer()
            for i in xrange(N):
                if message_length > 4096:
                    message = buffer(message_buffer, i, message_length)
                else:
                    message = message_buffer[i:i+message_length]
                bytecount += len(message)
                messenger.send(message, token, collector)
                sent_messages.append((message, token))
                l += 1
                if l % batch_size == 0:
                    replies = collector.collect()
                    for i in xrange(len(replies)):
                        rm, rt = replies[i]
                        sm, st = sent_messages.popleft()
                        if type(sm) is buffer:
                            rm = buffer(rm)
                        if rm != sm:
                            print 'i: ', i
                            assert False
                    collector = Collector(batch_size)

            end_time = timer()
            elapsed_time = end_time - start_time
            print 'Transmitted %d messages with a size of %d bytes' % (N, message_length)
            print 'Transmission time (with validation): %fs' % elapsed_time
            print '%.2f requests+replies/s, %.2f MB/s' % (float(N*2) / elapsed_time, (float(bytecount*2) / 2**20) / elapsed_time)
            messenger.close()
        finally:
            os.kill(p.pid, signal.SIGKILL)

if __name__ == '__main__':
    import unittest
    unittest.main()
