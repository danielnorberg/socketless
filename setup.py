from distutils.core import setup
from distutils.extension import Extension

modules = ['broadcast', 'channel', 'messenger', 'ropebuffer', 'streamserver']
extensions = [Extension('socketless.%s' % module, ['socketless/%s.c' % module]) for module in modules]

setup(
	name='socketless',
	version='0.1',
	packages=['socketless'],
    ext_modules = extensions,
)