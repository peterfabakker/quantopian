'''
    Allows the user to place in an order at say 12PM or whenever during the trading day
    and the trade will be executed at end-of-day
'''

from pytz import timezone
from datetime import datetime, timedelta
from zipline.utils.tradingcalendar import get_early_closes

def initialize(context):
    context.aapl = sid(24)
    
    # Initializing your start and end dates to check for early closes
    start_date = context.aapl.security_start_date
    end_date = context.aapl.security_end_date 
    context.early_closes = get_early_closes(start_date,end_date).date
    # Minutes before close that you want to execute your order, so this will execute at 3:55 PM only
    context.minutes_early = 5
    # Builds a queue for all orders to be executed at the end of the day
    context.order_queue = {}
   

def handle_data(context, data):
    
    # Adds an order to the queue to be executed at the end of the day 
    order_later(context.aapl, 5, context)
    # This executes all end of day orders
    endofday_activity(context, data)
    
    
    
def order_later(sid, amount, context):
    # Tracks the total amount of orders for each sid
    # So if the user orders 50 at multiple times in the day, it executes e.g. 200 at once 
    # not multiple orders
    if sid in context.order_queue:
        context.order_queue[sid] += amount
    else:
        context.order_queue[sid] = amount
        
def order_dequeue(context):
    # The order function that executes all orders in the order_queue
    for sid, amount in context.order_queue.items():
        log.info('About to execute ' + str(sid) + 'for ' + str(amount)) 
        order(sid, amount)

   
def endofday_activity(context, data):
    # Executes all checks and order activities, serves a similar purpose to handle_data
    # Checks if it's the end of day and then executes if True
    if endofday_check(context) == True:
        # Order_dequeue executes all orders in order_queue
        order_dequeue(context)
    else:
        pass
        
def endofday_check(context):
    # Converts all time-zones into US EST to avoid confusion
    loc_dt = get_datetime().astimezone(timezone('US/Eastern'))
    date = get_datetime().date()
    
    # Checks for an early close on special dates such as holidays and the day after thanksgiving
    # The market closes at 1:00PM EST on those days
    if date in context.early_closes:
    # Returns true if it's 1:00PM - minutes so in this case 12:55PM
        if loc_dt.hour == 12 and loc_dt.minute >= (60-context.minutes_early):
            if loc_dt.minute == 60-context.minutes_early:
                log.debug(get_datetime())
                return True
            else:
                # If the time is after 60-context.minutes_early, context.order_queue.clear() is cleared
                # so that any possible carryover into the next day is eliminated
                context.order_queue.clear()
                return False
        else:
            return False
    # Returns true if it's 4:00PM EST - minutes so in this case at 3:55PM
    # Daylight savings time are accounted for, so it will automatically adjust to DST           
    elif loc_dt.hour == 15 and loc_dt.minute >= (60-context.minutes_early):
        if loc_dt.minute == 60-context.minutes_early:
            log.debug(get_datetime())
            return True
        else:
            context.order_queue.clear()
            return False
    else:
        return False