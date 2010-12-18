from setuptools import setup
from setuptools.extension import Extension

modules = ['ropebuffer', 'broadcast', 'channel', 'messenger', 'streamserver']

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
    zip_safe=True,

	author = "Daniel Norberg",
    author_email = "daniel.norberg@gmail.com",
    url = "https://github.com/danielnorberg/socketless/",
    description = "Socketless: An asynchronous high performance TCP messaging library.",
	long_description = 	"""\
		Socketless is a an asynchronous TCP messaging library for
		implementing communication using messages and broadcast req/rep
		instead of raw sockets. Socketless relies on the library syncless
		to provide high-performance non-blocking sockets through utilization
		of epoll/kevent/kqueue. Socketless is implemented in Cython for high througput.
	""",
	license="Apache License, Version 2.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)