import subprocess
import argparse
import sys
import logging

from syncless.util import Queue
from syncless import coio

import paths

from socketless.channelserver import ChannelServer
from socketless.channel import DisconnectedException

def launch_echoserver(port, handshake=None):
	path = paths.path('test/utils/channel_echoserver.py')
	if handshake:
		challenge, response = handshake
		cmd = 'python %s %d %d -c "%s" -r "%s"' % (path, port, port, challenge, response)
	else:
		cmd = 'python %s %d %d' % (path, port, port)
	return subprocess.Popen(cmd, shell=True)

class EchoServer(ChannelServer):
	"""docstring for Handler"""
	def __init__(self, listener, handshake=None):
		super(EchoServer, self).__init__(listener)
		self.handshake = handshake
		logging.info('started')

	def sender(self, q, c, f):
		i = 0
		try:
			while True:
				i += 1
				message = q.popleft()
				if not message:
					break
				c.send(message)
				if len(q) == 0:
					c.flush()
		except DisconnectedException:
			pass
		finally:
			f.append(True)

	def receiver(self, q, c, f):
		i = 0
		try:
			while True:
				i += 1
				message = c.recv()
				q.append(message)
				if not message:
					break
		except DisconnectedException:
			logging.warning('Client disconnected')
		finally:
			f.append(True)

	def handle_connection(self, c, address):
		logging.info('New connection from %s:%s' % address)

		if self.handshake:
			expected_challenge, response = self.handshake
			logging.debug('Awaiting challenge.')
			challenge = c.recv()
			logging.debug('Got challenge: "%s"', challenge)
			if challenge == expected_challenge:
				logging.debug('Correct challenge, sending response: "%s"', response)
				c.send(response)
				c.flush()
				q = Queue()
				f = Queue()
				coio.stackless.tasklet(self.sender)(q, c, f)
				coio.stackless.tasklet(self.receiver)(q, c, f)
				f.popleft()
				f.popleft()
			else:
				logging.warning('Failed handshake!')
				logging.warning('Expected challenge: %s', expected_challenge)
				logging.warning('Actual challenge: %s', challenge)
		try:
			c.close()
			logging.info('Connection closed')
		except DisconnectedException:
			logging.warning('Client disconnected')


def main():

	parser = argparse.ArgumentParser(description="Echo Server")
	parser.add_argument('port_range_start', type=int)
	parser.add_argument('port_range_end', type=int)
	parser.add_argument('-d', '--debug', action='store_true')
	parser.add_argument('-c', '--challenge')
	parser.add_argument('-r', '--response')
	args = parser.parse_args()

	if args.debug:
		format = "%(asctime)-15s %(levelname)s (%(process)d) %(filename)s:%(lineno)d %(funcName)s(): %(message)s"
		logging.basicConfig(level=logging.DEBUG, format=format)
	else:
		logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

	handshake = (args.challenge, args.response)	if args.challenge and args.response else None
	if handshake:
		logging.info('Using handshake: %s -> %s' % handshake)
	if args.port_range_start == args.port_range_end:
		logging.info('Starting server on port %d' % args.port_range_start)
		EchoServer(('0.0.0.0', args.port_range_start), handshake=handshake).serve_forever()
	else:
		processes = [launch_echoserver(port, handshake=handshake) for port in xrange(args.port_range_start, args.port_range_end + 1)]
		while True:
			logging.info('q to quit')
			if raw_input() == 'q':
				break
		for process in processes:
			process.kill()
		sys.exit(0)


if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		print