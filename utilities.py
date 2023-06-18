import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime  
from datetime import timedelta
from pandas.tseries.offsets import DateOffset
from pandas.tseries.offsets import MonthEnd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import texts as txt

tickers = {    
    9999: '',
    4330: '4330: Riyad REIT',
    4331: '4331: Aljazira REIT',
    4332: '4332: Jadwa REIT Alharamain',
    4333: '4333: Taleem REIT',
    4334: '4334: Almaather REIT',
    4335: '4335: Musharaka REIT',
    4336: '4336: Mulkia Gulf REIT',
    4337: '4337: SICO Saudi REIT',
    4338: '4338: Alahli REIT',
    4339: '4339: Derayah REIT',
    4340: '4340: Alrajhi REIT',
    4342: '4342: Jadwa REIT',
    4344: '4344: SEDCO Capital REIT',
    4345: '4345: Alinma Retail REIT',
    4346: '4346: MEFIC REIT',
    4347: '4347: Bonyan REIT',
    4348: '4348: Alkhabeer REIT'
}

# global data columns
ticker_col = 'ticker'
year_col = 'year'
name_col = 'name'
shares_col = 'shares'
ffo_col = 'ffo'
dividend_col = 'dividend'
revenue_col = 'revenue'
interest_col = 'interest'
ebitda_col = 'ebitda'
ebit_col = 'ebit'
nav_col = 'nav'
asset_col = 'asset'
equity_col = 'equity'
casti_col = 'casti'
debt_col = 'debt'


pdata = pd.read_csv('data/pdata.csv')
pdata['date'] = pd.to_datetime(pdata['date'], format='%Y-%m-%d')

fdata = pd.read_csv('data/fdata.csv')
fdata[year_col] = pd.to_datetime(fdata[year_col], format='%Y-%m-%d')
fdata = fdata.sort_values(by=year_col)

def prep_ticker_timeseries_data(ticker):
    
    # get historical prices for input ticker
    ts = pdata[['date', str(ticker)]].rename(columns = {str(ticker):'price'})
    
    # get historical financials for input ticker
    df = fdata[[ticker_col, year_col, shares_col, ffo_col, dividend_col, nav_col]]
    
    # rolling agg on metrics for input ticker to obtain Trailing-12-Months (TTM) values
    df = df[df[ticker_col]==ticker].set_index(year_col).rolling(2).agg(
        {shares_col:'mean', ffo_col:'sum', dividend_col:'sum', nav_col:'mean'}).reset_index()
    
    df = df.rename(columns = {year_col:'period_end'})
    
    # DateOffset to subtract 6 months from period_end
    # MonthEnd to roll forward to the end of the given (0) month
    df['period_start'] = df['period_end'] - DateOffset(months=6) + MonthEnd(0)
    
    # merge metrcis to prices as per proper date range
    for i in [shares_col, ffo_col, dividend_col, nav_col]:
        ts[i] = np.piecewise(
            np.zeros(len(ts)),
            [(ts['date'].values >= period_start) & (ts['date'].values < period_end) \
             for period_start, period_end in zip(
                df['period_start'].values, df['period_end'].values)],
            np.append(df[i].values, np.nan))
        
    # forward fill data
    ts = ts.set_index('date').fillna(method='ffill').dropna()
    
    return ts

def compute_ticker_timeseries_metrics(ts):
    
    # compute output metrics
    ts['yield'] = 100 * (abs(ts[dividend_col]) / ts[shares_col]) / ts['price']
    ts['pffo'] = (ts['price'] * ts[shares_col]) / ts[ffo_col]
    ts['navpd'] = ((ts['price'] / ts[nav_col]) - 1) * 100
    
    # take only needed columns
    ts = ts[['price', nav_col, 'navpd', 'yield', 'pffo']]
    
    return ts

def get_ticker_timeseries(ticker):
    return compute_ticker_timeseries_metrics(prep_ticker_timeseries_data(ticker))

def get_sector_timeseries():
    df = pdata[['date']].set_index('date')
    df_yield = df.copy() 
    df_pffo = df.copy()
    
    for i in list(tickers)[1:]:
        df_aux = get_ticker_timeseries(i)
        df_yield[i] = df_aux['yield']
        df_pffo[i] = df_aux['pffo']
        
    df['yield'] = df_yield.median(axis=1)
    df['pffo'] = df_pffo.median(axis=1)

    return df

def prep_ticker_categorical_data(ticker, ttm=False):
    
    df = fdata[fdata[ticker_col] == ticker].drop(columns=[ticker_col, name_col])
    df['period'] = df[year_col].dt.year.astype(str) + '-' + df[year_col].dt.month.astype(str)
    df[year_col] = df[year_col].dt.year
            
    if ttm or df.shape[0] % 2:
        ttm = True
        df_aux = df.rolling(2).agg({
            shares_col: 'mean',
            ffo_col: 'sum',
            dividend_col: 'sum',
            revenue_col: 'sum',
            interest_col: 'sum',
            ebitda_col: 'sum',
            ebit_col: 'sum',
            nav_col: 'mean',
            asset_col: 'mean',
            equity_col: 'mean',
            casti_col: 'mean',
            debt_col: 'mean'})
    
    df = df[df.duplicated(year_col, keep=False) == True]

    df = df.groupby(year_col).agg({
        shares_col: 'mean',
        ffo_col: 'sum',
        dividend_col: 'sum',
        revenue_col: 'sum',
        interest_col: 'sum',
        ebitda_col: 'sum',
        ebit_col: 'sum',
        nav_col: 'last',
        asset_col: 'last',
        equity_col: 'last',
        casti_col: 'last',
        debt_col: 'last'})
    
    if ttm:
        df = pd.concat([df, df_aux.tail(1).rename(index={0: 'TTM'})])

    return df

def compute_ticker_categorical_metrics(df):
    
    '''
    Profitability and Efficiency Metrics
    '''
    df['ffos'] = df[ffo_col] / df[shares_col]
    df['ffo_payout'] = 100 * abs(df[dividend_col]) / df[ffo_col]
    df['ffo_margin'] = 100 * df[ffo_col] / df[revenue_col]
    df['ffo_roic'] = 100 * df[ffo_col] / (df[equity_col] + df[debt_col])
    
    '''
    Leverage and Coverage Metrics
    '''
    df['ffo_coverage'] = df[ffo_col] / abs(df[interest_col])
    df['ffo_leverage'] = (df[debt_col] - df[casti_col]) / df[ffo_col]
    
    # replace inf by zero
    # those with zero net_debt will get inf when computing metrics
    df.replace([np.inf, -np.inf], 0, inplace=True)
    
    return df

def get_ticker_categorical(ticker, ttm=False):
    return compute_ticker_categorical_metrics(
        prep_ticker_categorical_data(ticker, ttm))


####################################
####################################

var_dict = {
    'navpd': ' SAR',
    'yield': '%',
    'pffo': 'x',
    'ffos': '%.2f',
    'ffo_payout': '%.1f%%',
    'ffo_roic': '%.1f%%',
    'ffo_margin': '%.1f%%',
    'ffo_leverage': '%.2fx',
    'ffo_coverage': '%.2fx',
    }

color_dict = {
        'more_than_zero': {
            'navpd': '#ff2b2b',
            'pffo': '#ff2b2b',
            'yield': '#09ab3b'
        },
        'less_than_zero': {
            'navpd': '#09ab3b',
            'pffo': '#09ab3b',
            'yield': '#ff2b2b'
        }
    }

def display_divider():
    return st.markdown('<hr/>', unsafe_allow_html=True)

def display_text(text):
    return st.markdown(f'<p style="text-align: justify;">{text}</p>', unsafe_allow_html=True)

def display_metric(ticker_df, sector_df, metric):
     
     dic = {
        'navpd' : {
            'x': ticker_df['price'][-1],
            'y': ticker_df['nav'][-1],
            'z': ticker_df['navpd'][-1],
            'x_label': 'Current Price',
            'y_label': 'Current NAV',
            'unit': ' SAR', },
        'yield' : {
            'x': ticker_df.tail(1)['yield'][0],
            'y': sector_df.tail(1)['yield'][0],
            'z': (((ticker_df.tail(1)['yield'][0] / sector_df.tail(1)['yield'][0]) - 1) * 100),
            'x_label': 'Current Yield',
            'y_label': 'Sector Median Yield',
            'unit': '%', },
        'pffo' : {
            'x': ticker_df.tail(1)['pffo'][0],
            'y': sector_df.tail(1)['pffo'][0],
            'z': (((ticker_df.tail(1)['pffo'][0] / sector_df.tail(1)['pffo'][0]) - 1) * 100),
            'x_label': 'Current Multiple',
            'y_label': 'Sector Median Multiple',
            'unit': 'x', },
    } 
     
     output = f'''<div id="m_block">
                  <p id="m_value">{dic[metric]['x']:.2f}{dic[metric]['unit']}</p>
                  <p id="m_label">{dic[metric]['x_label']}</p>
                  <p id="m_value">{dic[metric]['y']:.2f}{dic[metric]['unit']}</p>
                  <p id="m_label">{dic[metric]['y_label']}</p>
                  <p id="m_value">{dic[metric]['z']:.2f}{'%'}</p>
                  <p id="m_label">{'Premium/Discount'}</p>
                  </div>'''
     return st.markdown(output, unsafe_allow_html=True)

def display_timeseries_chart(ticker_df, sector_df, metric):
    plt.rcParams['font.size'] = 6
    plt.rcParams['font.family'] = "sans-serif"
    plt.rcParams['text.color'] = "85868B"
    plt.rcParams['xtick.color'] = '85868B'

    if metric == 'navpd':
        xy = ticker_df['navpd']
    else:
        xy = ((ticker_df[metric] / sector_df[metric]) - 1) * 100

    x_curve = xy.index
    y_curve = xy.values 

    fig, ax = plt.subplots(figsize=(6.4, 1.2))

    ax.plot(ticker_df[metric], linewidth=0)

    ax.fill_between(x_curve, y_curve,
                    where=(y_curve > 0), color=color_dict['more_than_zero'][metric], alpha=0.15)
    ax.fill_between(x_curve, y_curve,
                    where=(y_curve < 0), color=color_dict['less_than_zero'][metric], alpha=0.15)

    ax.set_frame_on(False)
    ax.get_yaxis().set_visible(False)

    return st.pyplot(fig)

def display_categorical_chart(df, metric):
    plt.rcParams['font.size'] = 8
    plt.rcParams['font.family'] = "sans-serif"
    plt.rcParams['text.color'] = "262730"
    plt.rcParams['xtick.color'] = '262730'

    x = df.index
    y = df[metric]

    fig, ax = plt.subplots(figsize=(6.4, 4.5))
    bars = ax.bar(np.arange(len(x)), y, tick_label=x, color='#0068c9', width=0.96)
    ax.bar_label(bars, size=10,
                 padding=6, fmt=var_dict[metric],
                 bbox=dict(boxstyle="round, pad=0.3", fc="#0068c9", lw=0, alpha=0.10))
    
    ax.get_yaxis().set_visible(False)    
    ax.set_frame_on(False)
    
    plt.margins(x=0, y=0.15)
    plt.subplots_adjust(hspace=0)
    
    return st.pyplot(fig)

def display_categorical_section(ticker_df, metric):
    st.subheader(txt.headers[metric])
    display_text(txt.bodies[metric])
    display_categorical_chart(ticker_df, metric)
    display_divider()

def display_timeseries_section(ticker_df, sector_df, metric):
    st.subheader(txt.headers[metric])
    display_text(txt.bodies[metric])
    display_metric(ticker_df, sector_df, metric)
    display_timeseries_chart(ticker_df, sector_df, metric)
    display_divider()