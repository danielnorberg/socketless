# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-

import argparse
import time
import logging

from syncless import coio
from syncless.util import Queue

import paths

from socketless.messenger import Messenger
from socketless.broadcast import Broadcast

def invoke(broadcast, count, size, finished):
    message = '.' * size
    for i in xrange(count):
        replies = broadcast.send(message)
        assert set([token for reply, token in replies]) == set(token for token, messenger in broadcast.messengers)
        for reply, token in replies:
            # print token
            assert message == reply
    finished.append(True)

def main(ports, instances, count, size, handshake=None):
    hosts = [('localhost', port) for port in ports]
    message_count = instances * count * len(hosts)
    data_size = message_count * size
    total_data_size = 2 * data_size
    messengers = []
    try:
        start_time = time.time()
        tasklets = []
        finish_queue = Queue()
        for i in xrange(instances):
            messengers = [(id(host), Messenger(host, handshake=handshake)) for host in hosts]
            broadcast = Broadcast(messengers)
            tasklets.append(coio.stackless.tasklet(invoke)(broadcast, count, size, finish_queue))
        for i in xrange(instances):
            finish_queue.pop()
        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info('time: %.2f seconds', elapsed_time)
        logging.info('%.2f messages/s' % (float(message_count) / elapsed_time))
        logging.info('%.2f MB data' % (float(total_data_size) / (1024*1024)))
        logging.info('%.2f MB/s' % (float(total_data_size) / (1024*1024 * elapsed_time)))
    finally:
        for token, messenger in messengers:
            messenger.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Echo Client")
    parser.add_argument('port_range_start', type=int)
    parser.add_argument('port_range_end', type=int)
    parser.add_argument('instance_count', type=int)
    parser.add_argument('message_count', type=int)
    parser.add_argument('message_size', type=int)
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-c', '--challenge')
    parser.add_argument('-r', '--response')
    args = parser.parse_args()

    if args.debug:
        format = "%(asctime)-15s %(levelname)s (%(process)d) %(filename)s:%(lineno)d %(funcName)s(): %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=format)
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    ports = range(args.port_range_start, args.port_range_end+1)
    handshake = (args.challenge, args.response) if args.challenge and args.response else None
    if handshake:
        print 'Using handshake: %s -> %s' % handshake
    main(ports, args.instance_count, args.message_count, args.message_size, handshake=handshake)
