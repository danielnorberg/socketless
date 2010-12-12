import os

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
	Extension("ropebuffer", ["ropebuffer.pyx"]),
	Extension("test_ropebuffer_loop",
		sources = ["test_ropebuffer_loop.pyx"],
		include_dirs = [os.getcwd()],
	)
]

setup(
  name = 'ropebuffer',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)