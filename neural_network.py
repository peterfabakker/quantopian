import numpy
import random

'''
    This part is exclusively for the data simulation/learning part
'''

class FeedForwardNetwork:
      
    def __init__(self, nIn, nHidden, nOut, hw = [], ow = []):
        # learning rate
        self.alpha = 0.1
                                                  
        # number of neurons in each layer
        self.nIn = nIn
        self.nHidden = nHidden
        self.nOut = nOut
 
        if not hw == [] and not ow == []:
            # initialize weights with previous data
            self.hWeights = hw 
            self.oWeights = ow
         
        else: 
            # initialize weights randomly (+1 for bias)
            self.hWeights = numpy.random.random((self.nHidden, self.nIn+1)) 
            self.oWeights = numpy.random.random((self.nOut, self.nHidden+1))
          
        # activations of neurons (sum of inputs)
        self.hActivation = numpy.zeros((self.nHidden, 1), dtype=float)
        self.oActivation = numpy.zeros((self.nOut, 1), dtype=float)
          
        # outputs of neurons (after sigmoid function)
        self.iOutput = numpy.zeros((self.nIn+1, nOut), dtype=float)      # +1 for bias
        self.hOutput = numpy.zeros((self.nHidden+1, nOut), dtype=float)  # +1 for bias
        self.oOutput = numpy.zeros((self.nOut), dtype=float)
          
        # deltas for hidden and output layer
        self.hDelta = numpy.zeros((self.nHidden), dtype=float)
        self.oDelta = numpy.zeros((self.nOut), dtype=float)   
      
    def forward(self, input_node):
        # set input as output of first layer (bias neuron = 1.0)
        self.iOutput[:-1, 0] = input_node
        self.iOutput[-1:, 0] = 1.0
          
        # hidden layer
        self.hActivation = numpy.dot(self.hWeights, self.iOutput)
        self.hOutput[:-1, :] = numpy.tanh(self.hActivation)
          
        # set bias neuron in hidden layer to 1.0
        self.hOutput[-1:, :] = 1.0
          
        # output layer
        self.oActivation = numpy.dot(self.oWeights, self.hOutput)
        self.oOutput = numpy.tanh(self.oActivation)
      
    def backward(self, teach):
        error = self.oOutput - numpy.array(teach, dtype=float) 
          
        # deltas of output neurons
        self.oDelta = (1 - numpy.tanh(self.oActivation)) * numpy.tanh(self.oActivation) * error
                  
        # deltas of hidden neurons
        self.hDelta = (1 - numpy.tanh(self.hActivation)) * numpy.tanh(self.hActivation) * numpy.dot(numpy.transpose(self.oWeights[:,:-1]), self.oDelta)
                  
        # apply weight changes
#        print self.hWeights, self.hDelta, self.iOutput.transpose()
        self.hWeights = self.hWeights - self.alpha * numpy.dot(self.hDelta, numpy.transpose(self.iOutput)) 
        self.oWeights = self.oWeights - self.alpha * numpy.dot(self.oDelta, numpy.transpose(self.hOutput))
#        koiuh
    def getOutput(self):
        return self.oOutput
    
def hurst(p):
    tau = []; lagvec = []
    #  Step through the different lags
    for lag in range(2,20):
        #  produce price difference with lag
        pp = numpy.subtract(p[lag:],p[:-lag])
        #  Write the different lags into a vector
        lagvec.append(lag)
        #  Calculate the variance of the differnce vector
        tau.append(numpy.sqrt(numpy.std(pp)))
    #  linear fit to double-log graph (gives power)
    m = numpy.polyfit(numpy.log10(lagvec),numpy.log10(tau),1)
    # calculate hurst
    hurst = m[0]*2
    return hurst
 
def sharpe(series):
    ret = numpy.divide(numpy.diff(series),series[:-1])
    return(numpy.mean(ret)/numpy.std(ret))
    
def simulate_coint(d, n, mu, sigma, start_point_X, start_point_Y):
#  This becomes a random walk if d = 0
    X = numpy.zeros(n)
    Y = numpy.zeros(n)
    #  These are the starting points of the random walk in y
    #  Be aware that X and Y are NOT coordinates but diffent series
    X[0] = start_point_X
    Y[0] = start_point_Y
    for t in range(1,n):
        #  Drunk and his dog cointegration equations
        X[t] = X[t-1] + random.gauss(mu,sigma);
        Y[t] = d*(X[t-1] - Y[t-1]) + Y[t-1] + random.gauss(mu,sigma);
    return X,Y,X - Y
 
def simulate_momentum_data(n,offset,sigma):
#  This becomes a random walk if offset is 0
    # produce the trending time series
    return numpy.cumsum([random.gauss(offset,sigma) for i in range(n)])

 
def teach():
    k = random.randint(0, 2)
    if k == 0:
        dummy, dummy, F = simulate_coint(0.3, 1000, 0, 0.5, 0.0, 0.0)
    elif k == 1:
        F = simulate_momentum_data(1000,0.1,0.9)
    elif k == 2:
        F = simulate_momentum_data(1000,0,0.9)
    return k, sharpe(F[1:]), hurst(F[1:])

''' 
    Data simulation ends here and calculation of hurst and sharpe begin here
'''
# Setting up the constant window for data length
constant_window = 100

def initialize(context):
    context.spy = sid(8554)
    context.days_traded = 0
    context.past_prices = []

    
    context.hw = []
    context.ow = []
    context.ffn = FeedForwardNetwork(2,8,1, context.hw, context.ow)
    
def handle_data(context,data):
    # Over time, the score is decreasing which should be the opposite
    # What I'm thinking is that handle_data acts like the while loop

    gather_prices(context, data, context.spy)

    ''' 
        Network Learning Phase for context.days_traded < 100
    '''
    if (context.days_traded < constant_window):
        context.ffn = FeedForwardNetwork(2,8,1, context.hw, context.ow)
        true_count = 1
        untrue_count = 1
        uncertain_count = 1
        count = 0
        context.days_traded += 1
        while(count < 100):
            
            regime_desc, sharpe, hurst = teach()
            context.ffn.forward([sharpe, hurst])
            context.ffn.backward(regime_desc)
            
            f_output = context.ffn.getOutput()[0]
            
            if f_output >= 0.8 and regime_desc == 1: # Momentum data
                true_count +=1
            elif f_output <=0.2 and regime_desc == 0: # Mean Reverting
                true_count += 1
            elif f_output >=0.8 and regime_desc == 0 or f_output <0.2 and regime_desc==1:
                untrue_count += 1
            else:
                uncertain_count +=1
            total = float(uncertain_count) + float(true_count) + float(untrue_count)
            context.hw = context.ffn.hWeights
            context.ow = context.ffn.oWeights
            count +=1
    else:
        # As soon as the training wheels come it should be calibrated enough to launch
        log.debug("This is when the training wheels come off!")
        regime_desc, sharpe, hurst = teach()
        context.ffn.forward([sharpe, hurst])
        # Setting the correction at 0 because the training has already been done and we don't have a way to measure the corrections after this
        context.ffn.backward(0)

        f_output = context.ffn.getOutput()[0]
        h_output = hurst_r(context,data)

        momentum = True if (f_output > 0.8 and h_output > 0.5) else False

        reverting = True if (f_output < 0.2 and h_output < 0.2) else False

        avg_price = context.spy.mavg()

        ''' 
            So if the Hurst is less than 0.5 e.g. it means that the series will be moving in the opposite direction than before
            If the Hurst is greater than 0.5 then it will be moving in the same direction as before// How to get the direction of the previous series
            The question now is, how do we get the 
        '''

def gather_prices(context, data, sid):
    context.past_prices.append(data[sid].price)
    if len(context.past_prices) > constant_window:
        context.past_prices.pop(0)
    return 

'''
    Both hurst and sharpe will only return values if the length is greater than
    .80 * constant_window so in this case, 80 days
'''

def hurst_r(context, data):
    # Checks whether data exists
    if len(context.past_prices) < constant_window*.80:
        return
    
    tau, lagvec = [], []
    # Step through the different lags
    for lag in range(2,20):  
        # Produce price different with lag
        pp = numpy.subtract(context.past_prices[lag:],context.past_prices[:-lag])
        # Write the different lags into a vector
        lagvec.append(lag)
        # Calculate the variance of the difference
        tau.append(numpy.sqrt(numpy.std(pp)))
    # Linear fit to a double-log graph to get power
    m = numpy.polyfit(numpy.log10(lagvec),numpy.log10(tau),1)
    # Calculate hurst
    hurst = m[0]*2
    
    return hurst

def sharpe_r(context, data):
    # This sharpe takes the sharpe at the END of the period and not on a rolling basis
    if len(context.past_prices) < int(constant_window*.80):
        return
    returns = numpy.divide(numpy.diff(context.past_prices), context.past_prices[:-1])
    mean = numpy.mean(returns)
    std = numpy.std(returns)
    sharpe = mean/std
    # Sharpe * sqrt(number of periods in a year)
    return sharpe*numpy.sqrt(4)
