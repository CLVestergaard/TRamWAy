
from copy import deepcopy

class ConflictingVersionWarning(Warning):
	pass


class StorableHandler:
	'''Defines how to store an object of the class described by `Storable` `_parent`'''
	__slots__ = ['version', 'exposes', 'poke', 'peek', '_parent']

	@property
	def native_type(self):
		if self._parent is None:
			raise RuntimeError('corrupted handlers in Storable')
		else:	return self._parent.native_type

	@property
	def storable_type(self):
		if self._parent is None:
			raise RuntimeError('corrupted handlers in Storable')
		else:	return self._parent.storable_type

	def __init__(self, version=None, exposes={}, peek=None, poke=None):
		if version is None:
			version=(1,)
		self.version = version
		self.exposes = exposes
		self._parent = None
		self.peek = peek
		self.poke = poke



class Storable:
	'''Describes a storable class'''
	__slots__ = ['native_type', 'storable_type', '_handlers']

	@property
	def handlers(self):
		return self._handlers

	@handlers.setter
	def handlers(self, handlers):
		for h in handlers:
			h._parent = self
		self._handlers = handlers

	def __init__(self, python_type, key=None, handlers=[]):
		self.native_type = python_type
		self.storable_type = key
		if not isinstance(handlers, list):
			handlers = [handlers]
		self.handlers = handlers

	def hasVersion(self, version):
		return version in [ h.version for h in self.handlers ]
		
	def asVersion(self, version=None):
		return self.handlers[0] # not implemented yet!!!
		#if version:
		#	raise NotImplementedError
		#else:

	def poke(self, *vargs, **kwargs):
		self.asVersion(kwargs.pop('version', None)).poke(*vargs, **kwargs)

	def peek(self, *vargs, **kwargs):
		self.asVersion(kwargs.pop('version', None)).peek(*vargs, **kwargs)



class StorableService:
	__slots__ = ['by_native_type', 'by_storable_type']

	def __init__(self):
		self.by_native_type = {}
		self.by_storable_type = {}

	def registerStorable(self, storable, replace=False, agnostic=False):
		# check for compliance and fill in missing fields if possible
		if not all([ isinstance(h.version, tuple) for h in storable.handlers ]):
			raise TypeError('`Storable`''s version should be a tuple of numerical scalars')
		if storable.storable_type is None:
			module = storable.native_type.__module__
			name = storable.native_type.__name__
			if module is 'builtins':
				storable.storable_type = name
			elif module.endswith(name):
				storable.storable_type = module
			else:
				storable.storable_type = module + '.' + name
			if not agnostic:
				storable.storable_type = 'Python.' + storable.storable_type
		if not storable.handlers:
			raise ValueError('missing handlers', storable.storable_type)
		# get the existing storable with its handlers or make a storable with a single handler..
		if self.hasStorableType(storable.storable_type):
			existing = self.by_storable_type[storable.storable_type]
			if storable.native_type is not existing.native_type:
				raise TypeError('Storable type already exists')
		elif self.hasNativeType(storable.native_type):
			raise TypeError('Native type already exists')
		else:
			existing = deepcopy(storable)
			existing.handlers = []
		# .. and add the other/new handlers
		for h in storable.handlers:
			if existing.hasVersion(h.version):
				if replace:
					existing.handlers = [ h if h.version is h0.version else h0 \
						for h0 in existing.handlers ]
				else:
					warn((storable.storable_type, h.version), ConflictingVersionWarning)
			else:
				existing.handlers.append(h)
		# place/replace the storable in the double dictionary
		self.by_native_type[storable.native_type] = existing
		self.by_storable_type[storable.storable_type] = existing

	def byNativeType(self, t):
		return self.by_native_type[t]

	def hasNativeType(self, t):
		return t in self.by_native_type

	def byStorableType(self, t):
		return self.by_storable_type[t]

	def hasStorableType(self, t):
		return t in self.by_storable_type



class StoreBase(StorableService):
	'''Proxy class to `StorableService` that defines two abstract methods to be implemented for each concrete store'''
	__slots__ = ['storables']

	def __init__(self, storables):
		self.storables = storables

	@property
	def by_native_type(self):
		return self.storables.by_native_type

	@property
	def by_storable_type(self):
		return self.storables.by_storable_type

	def byNativeType(self, t):
		return self.storables.byNativeType(t)

	def hasNativeType(self, t):
		return self.storables.hasNativeType(t)

	def byStorableType(self, t):
		return self.storables.byStorableType(t)

	def hasStorableType(self, t):
		return self.storables.hasStorableType(t)

	def registerStorable(self, storable, **kwargs):
		self.storables.registerStorable(storable, **kwargs)

	def peek(self, objname, container):
		raise NotImplementedError('abstract method')

	def poke(self, objname, obj, container):
		raise NotImplementedError('abstract method')



def to_version(v):
	return tuple([ int(i) for i in v.split('.') ])

def from_version(v):
	s = '{:d}'
	s = s + ''.join( [ '.' + s ] * (len(v) - 1) )
	return s.format(*v)



class TypeErrorWithAlternative(TypeError):
	def __init__(self, instead_of, use):
		self.failing_type = instead_of
		self.suggested_type = use

	def __repr__(self):
		return '{} instead of {} use {}'.format(self.__class__, self.failing_type, self.suggested_type)

	def __str__(self):
		instead_of = self.failing_type
		use = self.suggested_type
		if isinstance(use, str):
			part1 = "use `{}` instead of `{}`".format(use, instead_of)
		else:
			s = "instead of `{}`, use any of the following:\n"
			s = ''.join([s] + [ "\t{}\n" ] * len(use))
			part1 = s.format(instead_of, *use)
			use = use[0]
		part2 = "If you can modify the parent class, please consider adding:\n" +\
			"\t@property\n" +\
			"\tdef _my_{}(self):\n" +\
			"\t\treturn # convert `my_{}` to `{}`\n" +\
			"\t@_my_{}.setter\n" +\
			"\t\tmy_{} = # convert `_my_{}` to `{}`\n" +\
			"and replace `my_{}` by `_my_{}` to the corresponding ReferenceHandler `exposes` attribute."
		part2 = part2.format(use, instead_of, use, use, instead_of, use, instead_of, instead_of, use)
		return part1 + part2


