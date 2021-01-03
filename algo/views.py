from django.shortcuts import render, redirect
from django.http import HttpResponse
from kiteconnect import KiteConnect
from . import models
import time
import pandas as pd
import ta
import yfinance as yf
import datetime as dt

request_token = ''
flag = ''
sd = models.site_data()
api_key = "66gpfzwyf4eigz86"
sd.api_key = api_key
kite = KiteConnect(api_key = api_key)

# Create your views here.
def algo_detail(request):
    
    ce = False
    pe = False
    condition = True
    try:
        stock = 'NIFTY 50'
        a = kite.instruments()
        a = pd.DataFrame(a)
        temp = a[(a['tradingsymbol'] == stock ) & (a['exchange'] == 'NSE')]
        instrument_token = int(temp['instrument_token'])
        ltp = int(pd.DataFrame(kite.ltp(instrument_token)).loc["last_price"])
        
        stock = "^NSEI"
        ticker = yf.Ticker(stock)
        data = ticker.history(period = "1mo")
        previous_day_close = data['Close'][-3]
        yesterday_close = data['Close'][-2]
        yesterday_high = data['High'][-2]
        yesterday_low = data['Low'][-2]

        last_day_range = round(yesterday_high.round(2) - yesterday_low.round(2),2)
        indicator = ta.trend.SMAIndicator(data['Close'],13)
        sma = indicator.sma_indicator()[-1]
        sma = sma.round(2)

        open_price = yesterday_close
        if yesterday_close < previous_day_close:
            pullback = True
        else:
            pullback = False

        if ltp>sma:
            trend='Upward'
            signal='buy'
            ce = True
            entry_price = open_price + 0.55 * last_day_range
            exit_price = yesterday_low
            if yesterday_close < previous_day_close:
                pullback = True
            else:
                pullback = False

        else:
            trend='Downward'
            signal='sell'
            pe = True
            entry_price = open_price - 0.55 * last_day_range
            exit_price = yesterday_high
            if yesterday_close > previous_day_close:
                pullback = True
            else:
                pullback = False

        option_name = get_option_symbol(ltp, ce, pe)

        sd.option_name = option_name

        temp = a[(a['tradingsymbol'] == option_name ) & (a['exchange'] == 'NFO')]
        sd.option_token = int(temp['instrument_token'])
        
        sd.ce = ce
        sd.pe = pe
        
        sd.entry_price = round(entry_price,2)
        sd.exit_price = round(exit_price,2)
        risk = "1%"

        context = {
                "condition":condition,
                "pullback":pullback,
                "trend":trend,
                "ltp":ltp,
                "sma":sma,
                "day_range":last_day_range,
                "api_key":sd.api_key,
                "access_token":sd.access_token,
                "instrument_token":instrument_token,
                "entry_price":round(entry_price,2),
                "exit_price":round(exit_price,2),
                "risk":risk,
                "signal":signal
            }
        return render(request, 'algo.html', context)
    except:
        return redirect('/start/')
        

        

def start(request):
    post = request.POST
    try:
        request_token = str(post['token'])
        
        
        api_secret = "c55wwbm0w6tk1gedexp2mn1e4xinab6q"
        sd.api_secret = api_secret
        data = kite.generate_session(request_token, api_secret = api_secret)
        access_token = data['access_token']
        if len(str(access_token)) > 0:
            sd.access_token = access_token
            kite.set_access_token(access_token)
            flag = 'SUCCESS'
        else:
            flag = 'FAILED'
    except:
        flag = 'FAILED'
   
    sd.login_url = kite.login_url()
    sd.flag = flag
    if flag=='SUCCESS':
        return redirect('/algo/')
    else:    
        return render(request, 'start.html', {'sd':sd})

def backtest(request):
    return render(request, 'algo.html')

def history(request):
    return render(request, 'algo.html')

def signal_buy(request):
    stoploss = sd.exit_price

    stock = 'NIFTY 50'
    a = kite.instruments()
    a = pd.DataFrame(a)
    temp = a[(a['tradingsymbol'] == stock ) & (a['exchange'] == 'NSE')]
    instrument_token = int(temp['instrument_token'])
    ltp = int(pd.DataFrame(kite.ltp(instrument_token)).loc["last_price"])
    
    a =pd.DataFrame(kite.margins())
    account_value = a.loc['net']['equity']

    quantity = account_value * 0.01 * 2 / (ltp - stoploss)
    lot_size = 75
    quantity = quantity/lot_size
    quantity = round(quantity,0)
    ltp_option = int(pd.DataFrame(kite.ltp(sd.option_token)).loc["last_price"])

    stoploss_option = ltp_option - (ltp-stoploss)/2

    try:
        kite.place_order(tradingsymbol=sd.option_name,
                                    exchange=kite.EXCHANGE_NFO,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                    quantity=quantity,
                                    order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_NRML,
                                    stoploss=stoploss_option,
                                    variety='regular')
    except:
        kite.place_order(tradingsymbol=sd.option_name,
                                    exchange=kite.EXCHANGE_NFO,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                    quantity=quantity,
                                    order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_NRML,
                                    stoploss=stoploss_option,
                                    variety='regular')
    

    return redirect('/algo/')


def get_option_symbol(current_price, ce, pe):
    current_price = str(current_price-current_price%100)
    #trading symbol format 'NIFTY20DEC12000CE'
    yr = str(dt.datetime.now().year)
    yr = yr[2:]
    
    month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 
              'AUG', 'SEP', 'OCT', 'NOV', 'DEC']              
    month_no = dt.datetime.now().month-1
    mnth = str(month_list[month_no])
    
    if ce:
        inst_type='CE'
    else:
        inst_type='PE'
        
    trading_symbol = 'NIFTY' + yr + mnth + current_price + inst_type
    return trading_symbol