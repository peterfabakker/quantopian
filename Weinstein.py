
rsi = ta.RSI(timeperiod=14)

def initialize(context):
    context.spy = sid(8554)
    context.max_notional = 1000000.1
    context.min_notional = -1000000.0
    
    context.past_rsi = {}
    context.past_prices = {}
    context.three_week_price = {}
    context.past_volume = {}
    
    # To be used for to see if stock falls into acceptable pattern
    context.w_checks = {'rsi': True, 'closing': True, 'volume_percent':True, 
                        'avg_volume':True, 'price_week': True}

def handle_data(context, data):
    # All the checks belong here in the first
    # RSI > RSI of five days ago
    # Closing price > closing price in last 30 days
    # Current volume > avg volume in last 60 days and at least 120% of the average
    # Current price > price in the last three weeks
    # Relative strength indicator greater than RSI of last five days
    rsi_data = rsi(data)
    current_rsi = rsi_data[context.spy]
    context.past_rsi[get_datetime().date()] = current_rsi  
    test_rsi = past_rsi(context,5)
    if current_rsi > test_rsi:
        context.w_checks['rsi'] = True
    else:
        context.w_checks['rsi'] = False
    
    # Closing price greater than the average closing price in last 30 days
    current_close = data[context.spy].close_price
    context.past_prices[get_datetime().date()] = data[context.spy].price
    current_close_mavg = closing_average(context, 30)
    if current_close > current_close_mavg and current_close_mavg > 0:
        context.w_checks['closing'] = True
    else:
        context.w_checks['closing'] = False
    
    #Volume greater than 120% of the last two months
    #Average volume in the last two months over 100,000
    current_volume = data[context.spy].volume
    context.past_volume[get_datetime().date()] = data[context.spy].volume
    current_volume_mavg = volume_average(context, 60)
    try:
        volume_percent = current_volume_mavg*1.2
    except:
        volume_percent = 0
    if current_volume > current_volume_mavg and current_volume_mavg > 0 and \
    current_volume > volume_percent:
        context.w_checks['avg_volume'] = True
    else:
        context.w_checks['avg_volume'] = False
    
    # Check if price today is greater than price in the past 3 weeks (21 days)
    context.three_week_price[get_datetime().date()] = data[context.spy].price
    context.w_checks['price_week'] = True
    for x,y in context.three_week_price.items():
        if current_close < y:
            context.w_checks['price_week'] = False
            break
    
    
    # Here should be where your order is. If false, then it hasn't passed the checks
    if False in context.w_checks.values(): 
        pass
    else:
        # Order here
        pass
           
                    
# Returns RSI from the user-specified days, note that if time period has been less than 14
# RSI returns numpy.null
def past_rsi(context, days):
    if len(context.past_rsi) > days:
        last = sorted(context.past_rsi.items(), key=lambda t: t[0])[0]
        try:
            del context.past_rsi[last[0]]
        except:
            return
    else:
        return
    return sorted(context.past_rsi.items(), key=lambda t: t[0])[0][1]

# Returns average closing price over the number of days specified by the user
def closing_average(context, days):
    # If the dictionary's length is over what we want to average over   
    if len(context.past_prices) > days:  
        # Find and remove the oldest entry  
        last = sorted(context.past_prices.items(), key=lambda t: t[0])[0]  
        del context.past_prices[last[0]]
    else:
        return

    # The 30-day moving average including most recent price from today  
    mavg = sum(context.past_prices.values())/len(context.past_prices)
    return mavg

# Returns average volume over the number of days specified by the user
def volume_average(context, days):
    if len(context.past_volume) >= days:
        last = sorted(context.past_volume.items(), key=lambda t:t[0])[0]
        del context.past_volume[last[0]]
    else:
        return
    mavg = sum(context.past_volume.values())/len(context.past_volume)
    return mavg

# Updates the context.three_week_price dictionary 
def three_week_price(context, days):
    if len(context.three_week_price) >= days:
        last = sorted(context.three_week_price.items(), key=lambda t: t[0])[0]
        del context.three_week_price[last[0]]
    else:
        return
    
