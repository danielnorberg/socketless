from syncless.util import Queue

class Broadcast(object):
	"""docstring for Broadcast"""
	def __init__(self, messengers):
		super(Broadcast, self).__init__()
		self.messengers = messengers
		self.q = Queue()

	def send(self, message):
		"""docstring for send"""
		for token, messenger in self.messengers:
			messenger.send(message, token, self.q)
		replies = [self.q.popleft() for messenger in self.messengers]
		return replies

	# def send_batch(self, messages):
	# 	"""docstring for send_batch"""
	# 	for message in messages:
	# 		for messenger in self.messengers:
	# 			messenger.send(message, self.q)
	# 	for i in xrange(len(self.messengers) * len(messages)):
	# 		yield self.q.get()

