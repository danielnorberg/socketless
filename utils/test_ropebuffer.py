import timeit

def	pure_run(N):
	from pure_ropebuffer import RopeBuffer
	b = RopeBuffer()
	for i in xrange(N):
		b.add('he')
		b.add('llo')
		b.add(' ')
		b.add('world')
		b.read(b.len)
		#
		# assert b.read(5) == 'hello'
		# assert b.read(6) == ' world'
		# assert b.len == 0

		# b = RopeBuffer()
		b.add('he')
		b.add('llo')
		b.add(' ')
		b.add('world')
		b.read(b.len)
		# assert b.read() == 'hello world'
		# assert b.len == 0


def main():
	N = 100000
	t = timeit.Timer("test_ropebuffer_loop.run(%d)" % (N),
	                       "import test_ropebuffer_loop")
	print "Cython loop", t.timeit(1), "sec"

	t = timeit.Timer("pure_run(%d)" % (N),
							"from __main__ import pure_run")
	print "Pure Python loop", t.timeit(1), "sec"

if __name__ == '__main__':
	main()