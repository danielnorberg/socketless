from setuptools import setup
from setuptools.extension import Extension

modules = ['broadcast', 'channel', 'messenger', 'ropebuffer', 'streamserver']

extensions = [Extension(
	name ='socketless.%s' % module,
	sources = ['socketless/%s.c' % module],
	extra_compile_args = ['-w'],
) for module in modules]

setup(
	name='socketless',
	version='0.1',
	packages=['socketless'],
    ext_modules = extensions,
	install_requires = ['syncless>=0.17'],
)