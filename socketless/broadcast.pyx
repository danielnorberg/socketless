__all__ = ['Broadcast']

from messenger cimport Messenger

from syncless.util import Queue

cdef class Broadcast:
	"""docstring for Broadcast"""
	def __init__(self, messengers):
		super(Broadcast, self).__init__()
		self.messengers = messengers
		self.q = Queue()

	cpdef send(self, message):
		"""docstring for send"""
		for token, messenger in self.messengers:
			messenger.send(message, token, self.q)
		replies = [self.q.popleft() for messenger in self.messengers]
		return replies
