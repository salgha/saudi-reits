import pandas as pd
import yfinance as yf
from datetime import datetime

def get_eod_price(ticker):
    t = '^' + ticker if ticker == 'trti' else ticker
    df = yf.Ticker(t+'.SR').history(period='1d', interval='1d')['Close'].reset_index()
    df['Date'] = pd.to_datetime(df['Date']).dt.floor('d').dt.tz_localize(None)
    df = df.rename(columns={'Date':'date', 'Close':ticker}).set_index('date')
    return df

tickers = ['4330', '4331', '4332', 
           '4333', '4334', '4335', 
           '4336', '4337', '4338', 
           '4339', '4340', '4342', 
           '4344', '4345', '4346', 
           '4347', '4348']

df = pd.read_csv('data/pdata.csv', index_col=0)
df.index = pd.to_datetime(df.index)

df_eod = get_eod_price('trti')

if df_eod.iloc[-1:].index.values not in df.index.values:
    for ticker in tickers:
        df_eod_aux = get_eod_price(ticker)
        df_eod = df_eod.merge(df_eod_aux, on='date', how='left')
        
    df = pd.concat([df, df_eod])
    
    df.round(2).to_csv('data/pdata.csv')