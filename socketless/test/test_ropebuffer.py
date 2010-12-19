import timeit
import unittest
from utils.testcase import TestCase

import paths

from socketless.ropebuffer import RopeBuffer

class RopeBufferTest(TestCase):
	def testBasic(self):
		b = RopeBuffer()
		b.add('he')
		b.add('llo')
		b.add(' ')
		b.add('world')
		assert b.read(5) == 'hello'
		assert b.read(6) == ' world'
		assert b.len == 0

		b.add('he')
		b.add('llo')
		b.add(' ')
		b.add('world')
		assert b.drain() == 'hello world'
		assert b.len == 0

if __name__ == '__main__':
	unittest.main()