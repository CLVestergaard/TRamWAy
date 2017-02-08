
import numpy as np
import pandas as pd

def isstructured(x):
	"""
	Check for named columns.

	The adjective *structured* comes from NumPy structured array.

	Arguments:
		x (any): any datatype

	Returns:
		bool: ``True`` if input argument ``x`` has named columns.

	"""
	if isinstance(x, pd.DataFrame) or isinstance(x, pd.Series):
		return True
	else:
		try:
			return False or x.dtype.names
		except AttributeError:
			return False

def columns(x):
	"""
	Get column names.

	Arguments:
		x (any): 
			datatype that satisfies :func:`isstructured`.

	Returns:
		iterable:
			``c`` satisfying ``x = x[c]``.

	Raises:
		ValueError: if no named columns are found in `x`.

	""" 
	if isinstance(x, pd.DataFrame):
		return x.columns
	elif isinstance(x, pd.Series):
		return x.index
	elif x.dtype.names:
		return x.dtype.names
	else:
		raise ValueError('not structured')
