''' 
    Attempt to initialize a neural network within Quantopian
'''
import numpy

#Defining window length for future batch_transforms
constant_window = 10

def initialize(context):
    context.past_prices = []
    context.spy = sid(8554)


def handle_data(context, data):
    gather_prices(context, data, context.spy)
    log.debug(sharpe(data, context))
    
# Arbtirary number just to clean up the data    
@batch_transform(window_length=constant_window)
def gather_data(data):
    return data


def gather_prices(context, data, sid):
    context.past_prices.append(data[sid].price)
    if len(context.past_prices) > constant_window:
        context.past_prices.pop(0)
    return 
    
'''
    Hurst exponent helps test whether the time series is:
    (1) A Random Walk (H ~ 0.5)
    (2) Trending (H > 0.5)
    (3) Mean reverting (H < 0.5)
'''
def hurst(context, data, sid):
    # Checks whether data exists
    data_gathered = gather_data(data)
    if data_gathered is None:
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

def sharpe(data, context):
    # This sharpe takes the sharpe at the END of the period and not on a rolling basis
    if len(context.past_prices) < int(constant_window*.80):
        return
    returns = numpy.divide(numpy.diff(context.past_prices), context.past_prices[:-1])
    mean = numpy.mean(returns)
    std = numpy.std(returns)
    sharpe = mean/std
    return sharpe


    
    