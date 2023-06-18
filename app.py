import streamlit as st
import utilities as utl
import matplotlib.pyplot as plt

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.title('Saudi REITs')
ticker = st.selectbox('Choose fund', utl.tickers.keys(),
                      label_visibility='collapsed', format_func=lambda x:utl.tickers[x])

sector_ts = utl.get_sector_timeseries()

if ticker != 9999:
    
    st.header(utl.tickers[ticker])

    ticker_ts = utl.get_ticker_timeseries(ticker)
    ticker_ct = utl.get_ticker_categorical(ticker)

    utl.display_timeseries_section(ticker_ts, sector_ts, 'navpd')
    utl.display_timeseries_section(ticker_ts, sector_ts, 'yield')
    utl.display_timeseries_section(ticker_ts, sector_ts, 'pffo')

    right, left = st.columns(2)
    with right:
        utl.display_categorical_section(ticker_ct, 'ffos')
    with left:
        utl.display_categorical_section(ticker_ct, 'ffo_payout')

    right, left = st.columns(2)
    with right:
        utl.display_categorical_section(ticker_ct, 'ffo_margin')
    with left:
        utl.display_categorical_section(ticker_ct, 'ffo_roic')

    right, left = st.columns(2)
    with right:
        utl.display_categorical_section(ticker_ct, 'ffo_coverage')
    with left:
        utl.display_categorical_section(ticker_ct, 'ffo_leverage')