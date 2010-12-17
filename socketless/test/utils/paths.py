import os, sys
home = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(home)

def path(_path):
	"""docstring for path"""
	return os.path.join(home, _path)
