# Global Market Rotation Strategy
import math
import pandas

def initialize(context):
    context.stocks = {12915: sid(12915), 21769: sid(21769),
                      24705: sid(24705), 23134: sid(23134),
                      23118: sid(23118), 23911: sid(23911)} 

    context.month = None
    context.period = 72 # 3 months period

def _order(stock, amount, price):
    if amount != 0:
        order(stock, amount)
        log.info("%s %d shares of %s = %.2f" % \
                 # If less than 0, it'll print out selling
                 (["buying", "selling"][amount<0], abs(amount),
                 stock.symbol, abs(price*amount)))


@batch_transform(window_length=73)
def get_metrics(dp, security, period):
    '''Calculate performance and volatility for given period.'''
    # Get's all the close prices of the security in the last 73 days (3 months)
    prices = dp['close_price'][security.sid][-period-1:]
    begin, end = prices[-period], prices[-1]
    volatility = (pandas.rolling_std(prices,20)*math.sqrt(period/20)).mean()
    return (end - begin)/begin, volatility/begin

def normalise(data, stocks, period):
    # Need to return normalised return and volume
    stocks_ret = {}
    stocks_vol = {}
    for stock in stocks.values():
        ret, vol = get_metrics(data, stock, period)
        stocks_ret[stock] = ret
        stocks_vol[stock] = vol
    # Return max = highest performance, while volatility max is lowest volatility
    ret_max, ret_min, vol_max, vol_min = max(stocks_ret.values()), min(stocks_ret.values()), \
                                        min(stocks_vol.values()), max(stocks_vol.values())
    return ret_max, ret_min, vol_max, vol_min
            

def sorted_by_rank(data, stocks, period):
    result = []
    ret_max, ret_min, vol_max, vol_min = normalise(data, stocks, period)
    for stock in stocks.values():
        ret, vol = get_metrics(data, stock, period)
        #log.debug('%s: return: %.2f, vol: %.2f' % (stock.symbol, ret, vol))
        ret = (ret-ret_min)/(ret_max-ret_min)
        vol = (vol-vol_min)/(vol_max-vol_min)
        rank = ret * 0.7 + vol * 0.3
        log.debug('%s: return: %.2f, vol: %.2f, rank: %.2f' % \
                  (stock.symbol, ret, vol, rank))
        result.append((rank, stock))
    return [stock for rank, stock in sorted(result, reverse=True)]

def handle_data(context, data):
    stocks = context.stocks
    month = data[stocks.values()[0]].datetime.month
    if not context.month:
        context.month = month

    ret = get_metrics(data, stocks.values()[0], context.period)
    # check if next month began
    if context.month == month:
        return
    context.month = month

    if ret:
        stocks = sorted_by_rank(data, stocks, context.period)
        #log.debug("The BEST 3 are: " + ', '.join(item.symbol for item in stocks[:3]))
        #stocks = stocks[0:1] # pick up first(the best)
        #stocks = stocks[1:2] # pick up second
        stocks = stocks[1:3] # pick up second and third ranked etfs
        sold = 0.0
        sids = [stock.sid for stock in stocks]

        # filter out already bought stocks
        positions = context.portfolio.positions
        stocks = [stock for stock in stocks \
                      if not positions[stock.sid]['amount']]
        
        # sell open positions except remaining winners
        sold = 0
        for position in positions.values():
            if position.amount and position.sid not in sids:
                pstock = context.stocks[position.sid]
                price = data[pstock].price
                _order(pstock, -position.amount, price)
                sold += position.amount * price
 
        # buy new winners if any
        
        if not stocks:
        #    log.debug("Winners are the same. Nothing to buy.")
        else:
            log.debug(stocks)
            for stock in stocks:
                amount = int((context.portfolio.cash+sold)/len(stocks)/data[stock].price)
                _order(stock, amount, data[stock].price)
                
                
                
''' The main question is, because you're using daily data, you don't exactly have an opening price ;
Otherwise you'd have to use minute data which is just way too slow.'''
 