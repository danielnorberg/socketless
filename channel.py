from utils.ropebuffer import RopeBuffer
import struct

class DisconnectedException(BaseException):
	pass

def read(s, b=1024*128):
	data = s.recv(b)
	if not data:
		raise DisconnectedException()
	return data

class Channel(object):
	"""docstring for Channel"""
	def __init__(self, socket):
		super(Channel, self).__init__()
		self.socket = socket
		self.f = self.socket.makefile()
		self.buffer = RopeBuffer()

	def send(self, message):
		try:
			self.f.write(struct.pack('!L', len(message)))
			self.f.write(message)
		except IOError:
			raise DisconnectedException()

	def flush(self):
		try:
			self.f.flush()
		except IOError:
			raise DisconnectedException()

	def recv(self):
		try:
			while self.buffer.len < 4:
				self.flush()
				self.buffer.add(read(self.socket))
			size = struct.unpack('!L', self.buffer.read(4))[0]
	 		if not size:
				self.flush()
				return None
			while self.buffer.len < size:
				self.flush()
				self.buffer.add(read(self.socket))
			message = self.buffer.read(size)
			return message
		except IOError:
			raise DisconnectedException()

	def close(self):
		self.send('')
		self.flush()
		self.f.close()
		self.f = None

