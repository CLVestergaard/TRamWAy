## see https://packaging.python.org/distributing/#setup-py

from setuptools import setup, find_packages
from codecs import open
from os import path

pwd = path.abspath(path.dirname(__file__))

## Get the long description from the README file
#with open(path.join(pwd, 'README.rst'), encoding='utf-8') as f:
#	long_description = f.read()

setup(
	name = 'inferencemap',
	version = '0.0.1',
	description = 'InferenceMAP',
	#long_description = long_description,
	url = 'https://github.com/influencecell/inferencemap',
	author = 'François Laurent',
	author_email = 'francois.laurent@pasteur.fr',
	license = 'MIT',
	classifiers = [
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.5',
	],
	keywords = '',
	packages = find_packages(exclude=['data', 'demo']),
	install_requires = ['six', 'numpy', 'scipy', 'pandas', 'tables', 'h5py'],
	extras_require = {},
	package_data = {},
	entry_points = {},
)
