
from math import *
import numpy as np
import numpy.linalg as la
from .graph import *
#from .graph.array import ArrayGraph
import matplotlib.pyplot as plt
import time


class Gas(Graph):
	"""Implementation of the Growing When Required clustering algorithm, first inspired from
	Marsland, S., Shapiro, J. and Nehmzow, U. (2002). A self-organising network that grows when required. Neural Networks 15, 1041-1058. doi: 10.1026/S0893-6080(02)00078-3
	and then extensively modified.

	Of note, :class:`Gas` features a :attr:`trust` attribute that enables faster learning when 
	inserting new nodes. Instead of inserting a node at `(w + eta) / 2` (with `trust == 0`) like in
	the standard algorithm, you can	insert sample point `eta` (with `trust == 1`) or any point in 
	between.
	:class:`Gas` also features a 'collapse' step at the end of each batch. This step consists of 
	merging nodes that are closer from each other than threshold :attr:`collapse_below`.
	Last but not least, the insertion threshold and collapse threshold can be functions of the 
	current training sample and nearest node.

	Implementation note: :class:`Gas` implements :class:`Graph` as a proxy, instanciating or taking
	another `Graph` object with optional input argument `graph` and delegates all :class:`Graph`'s 
	method to that object attribute.
	"""
	__slots__ = ['graph', 'insertion_threshold', 'trust', 'learning_rate', \
		'habituation_threshold', 'habituation_initial', 'habituation_alpha', \
		'habituation_tau', 'edge_lifetime', 'batch_size', 'collapse_below']

	def connect(self, n1, n2, **kwargs):
		self.graph.connect(n1, n2, **kwargs)
	def disconnect(self, n1, n2, edge=None):
		self.graph.disconnect(n1, n2, edge)
	def getNodeAttr(self, n, attr):
		return self.graph.getNodeAttr(n, attr)
	def setNodeAttr(self, n, **kwargs):
		self.graph.setNodeAttr(n, **kwargs)
	def getEdgeAttr(self, e, attr):
		return self.graph.getEdgeAttr(e, attr)
	def setEdgeAttr(self, e, **kwargs):
		self.graph.setEdgeAttr(e, **kwargs)
	@property
	def size(self):
		return self.graph.size
	def iterNodes(self):
		return self.graph.iterNodes()
	def iterNeighbors(self, n):
		return self.graph.iterNeighbors(n)
	def iterEdges(self):
		return self.graph.iterEdges()
	def iterEdgesFrom(self, n):
		return self.graph.iterEdgesFrom(n)
	def hasNode(self, n):
		return self.graph.hasNode(n)
	def addNode(self, **kwargs):
		return self.graph.addNode(**kwargs)
	def delNode(self, n):
		self.graph.delNode(n)
	def standsAlone(self, n):
		return self.graph.standsAlone(n)
	def findEdge(self, n1, n2):
		return self.graph.findEdge(n1, n2)
	def areConnected(self, n1, n2):
		return self.graph.areConnected(n1, n2)
	def export(self, **kwargs):
		return self.graph.export(**kwargs)
	def squareDistance(self, attr, eta, **kwargs):
		return self.graph.squareDistance(attr, eta, **kwargs)

	def __init__(self, sample, graph=None):
		if 1 < sample.shape[0]:
			w1 = sample[0]
			w2 = sample[-1]
		else:
			raise ValueError
		if graph:
			if isinstance(graph, type):
				self.graph = graph({'weight': None, 'habituation_counter': 0}, \
					{'age': 0})
			else:
				self.graph = graph
		else:
			from .graph.array import ArrayGraph # default implementation
			self.graph = ArrayGraph({'weight': None, 'habituation_counter': 0}, \
				{'age': 0})
		n1 = self.addNode(weight=w1)
		n2 = self.addNode(weight=w2)
		e  = self.connect(n1, n2)
		self.insertion_threshold = .95
		self.trust = 0 # in [0, 1]
		self.learning_rate = (.2, .006) # default values should be ok
		self.habituation_threshold = float('+inf') # useless, basically..
		self.habituation_initial = 1 # useless, basically..
		self.habituation_alpha = (1.05, 1.05) # should be greater than habituation_initial
		self.habituation_tau = (3.33, 14.33) # supposed to be time, but actually is to be
		# thought as a number of iterations; needs to be appropriately set
		self.edge_lifetime = 50 # may depend on the number of neighbors per node and 
		# therefore on the dimensionality of the data
		self.batch_size = 1000 # should be an order of magnitude or two below the total
		# sample size
		self.collapse_below = None

	def insertionThreshold(self, eta, node):
		"""Can be overwritten with:
		.. code-block:: python
			def insertion_threshold(eta, node):
				...
			gas.insertionThreshold = insertion_threshold
		"""
		##TODO: handle time more explicitly
		return self.insertion_threshold

	def collapseThreshold(self, eta, node):
		"""Same concept like :meth:`insertionThreshold`."""
		return self.collapse_below

	def habituationFunction(self, t, i=0):
		"""Returns the habituation for a given time/counter."""
		return self.habituation_initial - \
			(1 - exp(-self.habituation_alpha[i] * t / self.habituation_tau[i])) / \
			(self.habituation_alpha[i])

	def habituation(self, node, i=0):
		"""Returns the habituation of a node. Set `i=0` for the nearest node, 
		`i=1` for a neighbor of the nearest node."""
		return self.habituationFunction(float(self.getNodeAttr(node, 'habituation_counter')), i)

	def plotHabituation(self):
		##TODO: find a more general implementation for reading the habituations, and underlay
		# a histogram of the habituation counter in the graph
		if isinstance(self.graph, DictGraph):
			tmax = max(self.graph.nodes['habituation_counter'].values())
			tmax = round(float(tmax) / 100) * 100
		else:
			tmax = self.batch_size / 10
		t = np.arange(0, tmax)
		plt.plot(t, self.habituationFunction(t, 1), 'c-')
		plt.plot(t, self.habituationFunction(t, 0), 'b-')
		plt.xlim(0, tmax)
		plt.ylim(0, self.habituation_initial)
		plt.title('habituation function: alpha={}, tau={}'.format(self.habituation_alpha[0], \
				self.habituation_tau[0]))
		plt.ylabel('habituation')
		plt.xlabel('iteration number')

	def getWeight(self, node):
		return self.getNodeAttr(node, 'weight')

	def setWeight(self, node, weight):
		self.setNodeAttr(node, weight=weight)

	def incrementHabituation(self, node):
		count = self.getNodeAttr(node, 'habituation_counter') + 1
		self.setNodeAttr(node, habituation_counter=count)
		return count

	def incrementAge(self, edge):
		age = self.getEdgeAttr(edge, 'age') + 1
		self.setEdgeAttr(edge, age=age)
		return age

	def habituate(self, node):
		self.incrementHabituation(node)
		for edge, neighbor in list(self.iterEdgesFrom(node)):
			age = self.incrementAge(edge)
			self.incrementHabituation(neighbor) # increment before checking for age of the
			# corresponding edge, because `neighbor` may no exist afterwards; otherwise, to
			# increment after, it is necessary to check for existence of the node; should be
			# faster this way, due to low deletion rate
			if self.edge_lifetime < age:
				self.disconnect(node, neighbor, edge)
				if self.standsAlone(neighbor):
					self.delNode(neighbor)
		if self.standsAlone(node):
			self.delNode(node)

	def batchTrain(self, sample):
		"""This method grows the gas for a batch of data and implements the core GWR algorithm.
		:meth:`train` should be called instead."""
		eta_square = np.sum(sample * sample, axis=1)
		errors = []
		for k in np.arange(0, sample.shape[0]):
			eta = sample[k]
			# find nearest and second nearest nodes
			dist2, index_to_node = self.squareDistance('weight', eta, eta2=eta_square[k])
			i = np.argsort(dist2)
			dist_min = sqrt(dist2[i[0]])
			nearest, second_nearest = index_to_node(i[:2])
			errors.append(dist_min)
			# test activity and habituation against thresholds
			activity = exp(-dist_min)
			habituation = self.habituation(nearest)
			w = self.getWeight(nearest)
			if activity < self.insertionThreshold(eta, w) and \
				habituation < self.habituation_threshold:
				# insert a new node and connect it with the two nearest nodes
				self.disconnect(nearest, second_nearest)
				l = .5 + self.trust / 2 # mixing coefficient in the range [.5, 1]
				new_node = self.addNode(weight=(1.0 - l) * w + l * eta)
				self.connect(new_node, nearest)
				self.connect(new_node, second_nearest)
			else:
				# move the nearest node and its neighbors towards the sample point
				self.connect(nearest, second_nearest)
				self.setWeight(nearest, w + self.learning_rate[0] * habituation * (eta - w))
				for i in self.iterNeighbors(nearest):
					w = self.getWeight(i)
					self.setWeight(i, w + self.learning_rate[1] * \
						self.habituation(i, 1) * (eta - w))
			# update habituation counters
			self.habituate(nearest) # also habituates neighbors
		return errors

	def train(self, sample, pass_count=None, residual_max=None, error_count_tol=1e-6, \
		min_growth=None, collapse_tol=None, stopping_criterion=2, verbose=True, **kwargs):
		""":meth:`train` splits the sample into batches, successively calls :meth:`batchTrain` on
		these batches of data, collapses the gas if necessary and stops if stopping criteria are 
		met.
		The input arguments that define stopping criteria are:
		* `pass_count`: (min, max) numbers of times the algorithm should/can run on the full 
		sample.
		* `residual_max`: a residual is calculated for each sample point, before fitting the gas
		towards it, and `residual_max` is a threshold above which a residual is regarded as an
		'error'. This parameter works together with `error_count_tol`.
		* `error_count_tol`: maximum proportion of 'errors' (number of errors in a batch over the
		size of the batch). If this maximum is exceeded, then the :meth:`train` sample another
		batch and keeps on training the gas. Otherwise, the next criteria apply.
		* `min_growth`: minimum relative increase in the number of nodes from an iteration to the
		next.
		* `collapse_tol`: maximum allowed ratio of the number of collapsed nodes over the total
		number of nodes.
		* `stopping_criterion`: (provisional) `int`
			* `1`: performs a linear regression for the pre-fitting residual across time, and
			'tests' whether the trend is not negative.
			* `2`: stops if the average residual for the current batch is greater than that 
			of the previous batch.
		"""
		## TODO: clarify the code
		n = sample.shape[0]
		l = 0 # node count
		residuals = []
		if stopping_criterion is 1:
			import statsmodels.api as sm
		# if stopping_criterion is 2
		residual_mean = float('+inf')
		#
		if pass_count:
			p = .95
			#k1 = log(1 - p) / log(1 - 1 / float(n)) # sample size for each point to have probability p of being chosen once
			k1 = n
		if residual_max:
			if error_count_tol < 1:
				error_count_tol = ceil(error_count_tol * float(n))
		# loop
		t = []
		i = 0
		do = True
		while do:
			i += 1
			if verbose:
				t0 = time.time()
			r = self.batchTrain(sample[np.random.choice(n, size=self.batch_size),:])
			residuals += r
			l_prev = l
			l = self.size
			txt = l
			if self.collapse_below:
				self.collapse()
				dl = l - self.size
				if verbose and 0 < dl:
					txt = '{} (-{})'.format(l, dl)
			if verbose:
				if i is 1:
					if self.collapse_below:
						print("\t#nodes (-#collapsed)")
					else:	print("\t#nodes")
				ti = time.time() - t0
				t.append(ti)
				print("{}\t{}\tElapsed: {:.0f} ms".format(i, txt, ti * 1e3))
			# enforce some stopping or continuing conditions
			if pass_count:
				k = i * self.batch_size
				if k < pass_count[0] * k1:
					continue
				elif pass_count[1] * k1 <= k:
					if verbose:
						print('upper bound for `pass_count` reached')
					break # do = False
			if residual_max:
				error_count = len([ residual for residual in r
						if residual_max < residual ])
				if error_count_tol < error_count:
					continue
			if min_growth is not None:
				growth = float(l - l_prev) / float(l_prev)
				if growth < min_growth:
					if verbose:
						print('relative growth: {:.0f}%'.format(growth * 100))
					break
			if self.collapse_below and collapse_tol:
				collapse_rel = float(dl) / float(l)
				if collapse_tol < collapse_rel:
					if verbose:
						print('relative collapse: {:.0f}%'.format(collapse_rel * 100))
					break
			# exclusive criteria
			if stopping_criterion is 1:
				regression = sm.OLS(np.array(r), \
						sm.add_constant(np.linspace(0,1,len(r)))\
					).fit()
				if 0 < regression.params[1]:
					fit = 0
				else:
					fit = 1/(1+exp((.1-regression.pvalues[1])/.01)) # invert p-value
				do = tolerance < fit
			elif stopping_criterion is 2:
				residual_prev = residual_mean
				#_, r = self.eval(sample[np.random.choice(n, size=self.validation_batch_size),:])
				residual_mean = np.mean(r)
				residual_std  = np.std(r)
				do = (residual_mean - residual_prev) / residual_std < 0
		if verbose:
			t = np.asarray(t)
			print('Elapsed:  mean: {:.0f} ms  std: {:.0f} ms'.format(np.mean(t) * 1e3, \
									np.std(t) * 1e3))
		return residuals

	def collapse(self):
		for n in list(self.iterNodes()):
			if self.hasNode(n):
				neighbors = [ neighbor for neighbor in self.iterNeighbors(n)
							if n < neighbor ]
				if neighbors:
					dist = la.norm(self.getWeight(n) - \
						np.vstack([ self.getWeight(n)
							for n in neighbors ]), axis=1)
					k = np.argmin(dist)
					if dist[k] < self.collapse_below:
						neighbor = neighbors[k]
						#print((n, neighbor))
						self.collapseNodes(n, neighbor)

	def collapseNodes(self, n1, n2):
		self.disconnect(n1, n2)
		w1 = self.getWeight(n1)
		w2 = self.getWeight(n2)
		self.setWeight(n1, (w1 + w2) / 2)
		for e2, n in list(self.iterEdgesFrom(n2)):
			a2 = self.getEdgeAttr(e2, 'age')
			e1 = self.findEdge(n1, n)
			if e1 is None:
				self.connect(n1, n, age=a2)
			else:
				a1 = self.getEdgeAttr(e1, 'age')
				self.setEdgeAttr(e1, age=min(a1, a2))
			#self.disconnect(n2, n, e2)
		self.delNode(n2)

