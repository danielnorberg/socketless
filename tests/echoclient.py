from syncless import coio
from syncless.util import Queue

import argparse
import time

import sys
import paths
sys.path.append(paths.home)

from messenger import Messenger
from broadcast import Broadcast

def invoke(broadcast, count, size, finished):
	message = '.' * size
	for i in xrange(count):
		replies = broadcast.send(message)
		assert set([token for reply, token in replies]) == set(token for token, messenger in broadcast.messengers)
		for reply, token in replies:
			# print token
			assert message == reply
	finished.append(True)

def main(ports, instances, count, size):
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
			messengers = [(id(host), Messenger(host)) for host in hosts]
			broadcast = Broadcast(messengers)
			tasklets.append(coio.stackless.tasklet(invoke)(broadcast, count, size, finish_queue))
		for i in xrange(instances):
			finish_queue.pop()
		end_time = time.time()
		elapsed_time = end_time - start_time
		print 'time: %.2f seconds' % elapsed_time
		print '%.2f messages/s' % (float(message_count) / elapsed_time)
		print '%.2f MB data' % (float(total_data_size) / (1024*1024))
		print '%.2f MB/s' % (float(total_data_size) / (1024*1024 * elapsed_time))
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
	args = parser.parse_args()

	ports = range(args.port_range_start, args.port_range_end+1)
	main(ports, args.instance_count, args.message_count, args.message_size)