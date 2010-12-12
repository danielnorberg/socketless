from pure_ropebuffer import RopeBuffer

def	pure_run(N):
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
	run(1000000)

if __name__ == '__main__':
	main()