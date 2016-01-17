from numpy import sqrt,sqrt,array,unravel_index,nditer,linalg,random,subtract,power,exp,pi,zeros,arange,outer,meshgrid,linspace,log,where
from collections import defaultdict
from warnings import warn
#import time
import sys
"""
    Minimalistic implementation of the Self Organizing Maps (SOM).

    Giuseppe Vettigli 2013.
"""

class MiniSom:
    def __init__(self,x,y,input_len,sigma=1.0,learning_rate=0.5,random_seed=None, bmuFeatures=None):
        """
            Initializes a Self Organizing Maps.
            x,y - dimensions of the SOM
            input_len - number of the elements of the vectors in input
            sigma - spread of the neighborhood function (Gaussian), needs to be adequate to the dimensions of the map.
            (at the iteration t we have sigma(t) = sigma / (1 + t/T) where T is #num_iteration/2)
            learning_rate - initial learning rate
            (at the iteration t we have learning_rate(t) = learning_rate / (1 + t/T) where T is #num_iteration/2)
            random_seed, random seed to use.
        """
        if sigma >= x/2.0 or sigma >= y/2.0:
            warn('Warning: sigma is too high for the dimension of the map.')
        if random_seed:
            self.random_generator = random.RandomState(random_seed)
        else:
	    #print random_seed
            self.random_generator = random.RandomState(random_seed)
        self.learning_rate = learning_rate
        self.sigma = sigma
        self.weights = self.random_generator.rand(x,y,input_len)*2-1 # random initialization
        self.weights = array([v/linalg.norm(v) for v in self.weights]) # normalization
        self.activation_map = zeros((x,y))
        self.neigx = arange(x)
        self.neigy = arange(y) # used to evaluate the neighborhood function
        self.neighborhood = self.gaussian
        self.x = x
        self.y = y 
        self.input_len = input_len
        self.tick = 0
        self.ticks = 0
        self.running = False
        self.paused = False
        self.bmuFeatures = bmuFeatures # for matching BMUs (finding winner) based on subset


    def _activate(self,x):
        """ Updates matrix activation_map, in this matrix the element i,j is the response of the neuron i,j to x """
        # if not matching based on subset of features
        if self.bmuFeatures == None: 
            s = subtract(x,self.weights) # x - w
        else:
            # print( x.shape, self.weights.shape)
            s = subtract(x[:-2],self.weights[:,:,:-2] ) 

        it = nditer(self.activation_map, flags=['multi_index'])
        while not it.finished:
            self.activation_map[it.multi_index] = linalg.norm(s[it.multi_index]) # || x - w ||
            it.iternext()
	
    def activate(self,x):
        """ Returns the activation map to x """
        self._activate(x)
        return self.activation_map


    def gaussian(self,c,sigma):
        """ Returns a Gaussian centered in c """
        d = 2*pi*sigma*sigma
        ax = exp(-power(self.neigx-c[0],2)/d)
        ay = exp(-power(self.neigy-c[1],2)/d)
        return outer(ax,ay) # the external product gives a matrix

    def diff_gaussian(self,c,sigma):
        """ Mexican hat centered in c (unused) """
        xx,yy = meshgrid(self.neigx,self.neigy)
        p = power(xx-c[0],2) + power(yy-c[1],2)
        d = 2*pi*sigma*sigma
        return exp(-(p)/d)*(1-2/d*p)

    def winner(self,x ):
        """ Computes the coordinates of the winning neuron for the sample x
		  """
        self._activate(x)
        return unravel_index(self.activation_map.argmin(),self.activation_map.shape)

    def update(self,x,win,t):
        """
            Updates the weights of the neurons.
            x - current pattern to learn
            win - position of the winning neuron for x (array or tuple).
            t - iteration index
        """
        # print( 'in update, this is x going into quanitization error fct', x ) # HERE
        # q = self.quantization_error(x)  # originally
        # SR fixed a bug.  passing x to quantization_error function
        #   actually gets difference to individual features.
        # q = self.quantization_error([x])

        # eta(t) = eta(0) / (1 + t/T) 
        # keeps the learning rate nearly constant for the first T iterations and then adjusts it
        eta = self.learning_rate/(1+t/self.T)
        sig = self.sigma/(1+t/self.T) # sigma and learning rate decrease with the same rule
        g = self.neighborhood(win,sig)*eta # improves the performances
        it = nditer(g, flags=['multi_index'])
        while not it.finished:
            # eta * neighborhood_function * (x-w)
            self.weights[it.multi_index] += g[it.multi_index]*(x-self.weights[it.multi_index])            
            # normalization
            self.weights[it.multi_index] = self.weights[it.multi_index] / linalg.norm(self.weights[it.multi_index])
            it.iternext()

           
    def update_gliozzi(self,x,win,t):
        """
            Updates the weights of the neurons.
            x - current pattern to learn
            win - position of the winning neuron for x (array or tuple).
            t - iteration index
        """
        # p. 722 Gliozzi et al. (2009)
        ## eta(t) = 1 / (1 + exp( - (quantization_error(d) - beta) / alpha))
        q = self.quantization_error(x)


        #alpha = 0.2
        #beta = .4
        #eta = 1 / (1 + exp( -( (q - beta) / alpha)))
        #eta = 0.25


 

	#From MIOsom_seqtrainBISPESATOESP1RETE.m
	#val_x1 = 0.7
	#val_x2 = 1
	#val_y1=0.5
	#val_y2=1
	#coeff_b= (log(val_y2) - log(val_y1))/ (val_x2 - val_x1)
	#coeff_a = val_y1 * exp(-coeff_b * val_x1)
        #eta = max(0.1, min(1, coeff_a*exp(coeff_b*sqrt(q))))

	# display x, q 	
	print "x = ", x, "qerr = ", q
	
	
	#From MIOsom_seqtrainBISPESATOESP1RETTOT.m
	#val_y1=0.5;
	#val_y2=1;
	#coeff_b= (log(val_y2) - log(val_y1))/ (val_x2 - val_x1);
	#coeff_a = val_y1 * exp(-coeff_b * val_x1);
  
	#lrate = 1/(1 + exp(-((sqrt(qerr)-val_05)/steepness)));
	r =   12
	val_05 = 0.1 + r * 0.05
	steepness = 0.1 + r * 0.05
	
	
	eta =  1 / (1 + exp(-((sqrt(q)-val_05)/steepness)));
	
	print "lrate = ", eta

        #sig = self.sigma
        #g = self.neighborhood(win,self.sigma_gliozzi[t])*eta # improves the performances


        g = self.neighborhood(win,self.sigma_gliozzi[t])*eta # improves the performances
        it = nditer(g, flags=['multi_index'])
        while not it.finished:
            # eta * neighborhood_function * (x-w)
            self.weights[it.multi_index] += g[it.multi_index]*(x-self.weights[it.multi_index])            
            # normalization
            #self.weights[it.multi_index] = self.weights[it.multi_index] / linalg.norm(self.weights[it.multi_index])
            it.iternext()

    def quantization(self,data):
        """ Assigns a code book (weights vector of the winning neuron) to each sample in data. """
        q = zeros(data.shape)
        for i,x in enumerate(data):
            q[i] = self.weights[self.winner(x)]
        return q

    #def sample_weights_gliozzi(self,data):

    def weights_init_gliozzi(self,data):
      
        """ Initializes the weights of the SOM picking random samples from data """
        #it = nditer(self.activation_map, flags=['multi_index'])
        
        #self.sample_weights_gliozzi(data)
        #while not it.finished:
	    #for i in range(8):

	    #self.weights[it.multi_index][i] = self.random_generator.uniform(min(data[:,i]), max(data[:,i])) *0.3
	    #self.weights[it.multi_index][i] = data[:,i]
            ##self.weights[it.multi_index] = self.weights[it.multi_index]/linalg.norm(self.weights[it.multi_index])
            #it.iternext()
	""" Initializes the weights of the SOM picking random samples from data """


        it = nditer(self.activation_map, flags=['multi_index'])
        scale = 0.3
        while not it.finished:
	    #for i in range(8):
	    for i in range(self.input_len):
	      col = data[:, i]
	      self.weights[it.multi_index][i] = self.random_generator.uniform(min(col), max(col)) * scale
	     
            it.iternext()

    def random_weights_init(self,data):
        """ Initializes the weights of the SOM picking random samples from data """
        it = nditer(self.activation_map, flags=['multi_index'])
        while not it.finished:
            self.weights[it.multi_index] = data[int(self.random_generator.rand()*len(data)-1)]
            self.weights[it.multi_index] = self.weights[it.multi_index]/linalg.norm(self.weights[it.multi_index])
            it.iternext()

    def train_random(self,data,num_iteration):
        self.running = True
        """ Trains the SOM picking samples at random from data """
        self._init_T(num_iteration)      
        for iteration in range(num_iteration):
            rand_i = int(round(self.random_generator.rand()*len(data)-1)) # pick a random sample
            self.update(data[rand_i],self.winner(data[rand_i]),iteration)
            
        self.running = False

            
    def train_random_once(self,data):    
        self.running = True

        """ Trains the SOM picking samples at random from data """
        data_indices = range(len(data))
        self._init_T(len(data))      

        random.shuffle(data_indices)
        #print( data_indices ) # HERE

        for iteration, d in enumerate(data_indices):
            #print( data.shape ) #HERE
            self.update(data[d],self.winner(data[d]),iteration)
        self.running = False

            
    def train_gliozzi(self,data,num_iteration=1):    
      	self.running = True

        """ Trains the SOM picking samples at random from data """
	data_indices = range(len(data))
	self.sigma_gliozzi = linspace(1.2, 0.8, num=len(data))

	self._init_T(len(data))      

        #while iteration < num_iteration:

	random.shuffle(data_indices)
	for iteration, d in enumerate(data_indices):
          self.update_gliozzi(data[d],self.winner(data[d]),iteration)
          
        self.running = False


    def train_batch(self,data,num_iteration):
	self.running = True
        """ Trains using all the vectors in data sequentially """
        self._init_T(len(data)*num_iteration)
        iteration = 0
        while iteration < num_iteration:
            idx = iteration % (len(data)-1)
            self.update(data[idx],self.winner(data[idx]),iteration)
            iteration += 1
        self.running = False

    def _init_T(self,num_iteration):
        """ Initializes the parameter T needed to adjust the learning rate """
        self.T = num_iteration/2 # keeps the learning rate nearly constant for the first half of the iterations

    def distance_map(self):
        """ Returns the average distance map of the weights.
            (Each mean is normalized in order to sum up to 1) """
        um = zeros((self.weights.shape[0],self.weights.shape[1]))
        it = nditer(um, flags=['multi_index'])
        while not it.finished:
            for ii in range(it.multi_index[0]-1,it.multi_index[0]+2):
                for jj in range(it.multi_index[1]-1,it.multi_index[1]+2):
                    if ii >= 0 and ii < self.weights.shape[0] and jj >= 0 and jj < self.weights.shape[1]:
                        um[it.multi_index] += linalg.norm(self.weights[ii,jj,:]-self.weights[it.multi_index])
            it.iternext()
        um = um/um.max()
        return um

    def activation_response(self,data):
        """ 
            Returns a matrix where the element i,j is the number of times
            that the neuron i,j have been winner.
        """
        a = zeros((self.weights.shape[0],self.weights.shape[1]))
        for x in data:
            a[self.winner(x)] += 1
        return a

    def quantization_error(self,data):
        """ 
            Returns the quantization error computed as the average distance between
            each input sample and its best matching unit.            
        """
        
        # print( 'In quantization_error, this is data looped through', data)
        error = 0
        for x in data:
            # print( 'data vector being tested in quantization_error fct',x ) #HERE
            error += linalg.norm(x-self.weights[self.winner(x)])
        return error/len(data)
      
    def quantization_error_subset(self,data,n):
        """ 
            Returns the quantization error computed as the average distance between
            each input sample and its best matching unit.            
        """
        #n = cols -1
        
        tmp = data[0:n]
        data = tmp
        error = 0
        for x in data:
            error += linalg.norm(x-self.weights[self.winner(x)])
        return error/len(data)
  
    def win_map(self,data):
        """
            Returns a dictionary wm where wm[(i,j)] is a list with all the patterns
            that have been mapped in the position i,j.
        """
        winmap = defaultdict(list)
        for x in data:
            winmap[self.winner(x)].append(x)
        return winmap

'''
    def pertSomWeights( self, scale == None):
    	if scale == None:
    	scale = .5
    	print( 'Adding noise to SOM weights')

    	pertAmount = scale*(np.random.random_sample( self.som.weights.shape)-.5)
    	self.weights = self.weights + pertAmount

    def pertInputs( self,  widget=None, data=None ):
    	#if scale == None:
    	p = .2
        print( 'Making %f prop of inputs 0.5' %p)
    	#print( self.data.shape )

    	# randomly get indices to switch, then replace
    	noiseIndex = np.random.binomial(1,p, self.data.shape)  #ones at p proportion of samples
    	self.data[noiseIndex ==1 ] = .5
    	#print( self.data )
'''

### unit tests
from numpy.testing import assert_almost_equal, assert_array_almost_equal, assert_array_equal

class TestMinisom:
    def setup_method(self, method):
        self.som = MiniSom(5,5,1)
        for w in self.som.weights: # checking weights normalization
            assert_almost_equal(1.0,linalg.norm(w))
        self.som.weights = zeros((5,5)) # fake weights
        self.som.weights[2,3] = 5.0
        self.som.weights[1,1] = 2.0

    def test_gaussian(self):
        bell = self.som.gaussian((2,2),1)
        assert bell.max() == 1.0
        assert bell.argmax() == 12  # unravel(12) = (2,2)

    def test_win_map(self):
        winners = self.som.win_map([5.0,2.0])
        assert winners[(2,3)][0] == 5.0
        assert winners[(1,1)][0] == 2.0

    def test_activation_reponse(self):
        response = self.som.activation_response([5.0,2.0])
        assert response[2,3] == 1
        assert response[1,1] == 1

    def test_activate(self):
        assert self.som.activate(5.0).argmin() == 13.0  # unravel(13) = (2,3)
     
    def test_quantization_error(self):
        self.som.quantization_error([5,2]) == 0.0
        self.som.quantization_error([4,1]) == 0.5

    def test_quantization(self):
        q = self.som.quantization(array([4,2]))
        assert q[0] == 5.0
        assert q[1] == 2.0

    def test_random_seed(self):
        som1 = MiniSom(5,5,2,sigma=1.0,learning_rate=0.5,random_seed=1)
        som2 = MiniSom(5,5,2,sigma=1.0,learning_rate=0.5,random_seed=1)
        assert_array_almost_equal(som1.weights,som2.weights) # same initialization
        data = random.rand(100,2)
        som1 = MiniSom(5,5,2,sigma=1.0,learning_rate=0.5,random_seed=1)
        som1.train_random(data,10)
        som2 = MiniSom(5,5,2,sigma=1.0,learning_rate=0.5,random_seed=1)
        som2.train_random(data,10)
        assert_array_almost_equal(som1.weights,som2.weights) # same state after training

    def test_train_batch(self):
        som = MiniSom(5,5,2,sigma=1.0,learning_rate=0.5,random_seed=1)
        data = array([[4,2],[3,1]])
        q1 = som.quantization_error(data)
        som.train_batch(data,10)
        assert q1 > som.quantization_error(data)

    def test_train_random(self):
        som = MiniSom(5,5,2,sigma=1.0,learning_rate=0.5,random_seed=1)
        data = array([[4,2],[3,1]])
        q1 = som.quantization_error(data)
        som.train_random(data,10)
        assert q1 > som.quantization_error(data)

    def test_random_weights_init(self):
        som = MiniSom(2,2,2,random_seed=1)
        som.random_weights_init(array([[1.0,.0]]))
        for w in som.weights:
            assert_array_equal(w[0],array([1.0,.0]))



