cimport ropebuffer
import ropebuffer

def	run(N):
	cdef int i
	cdef ropebuffer.RopeBuffer b = ropebuffer.RopeBuffer()
	for i in xrange(N):
		b.add('he')
		b.add('llo')
		b.add(' ')
		b.add('world')
		# assert b.read(5) == 'hello'
		# assert b.read(6) == ' world'
		# assert b.len == 0
		b.read(b.len)

		# b = RopeBuffer()
		b.add('he')
		b.add('llo')
		b.add(' ')
		b.add('world')
		# assert b.read(b.len) == 'hello world'
		# assert b.len == 0
		b.read(b.len)
