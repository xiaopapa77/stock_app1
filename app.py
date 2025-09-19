import streamlit as st
import yfinance as yf
import pandas as pd

def highlight_diff(val):
    if pd.isna(val):
        return ''
    elif val > 0:
        return 'background-color: #cc6666; color: white;'
    elif val < 0:
        return 'background-color: #669966; color: white;'
    else:
        return ''

st.set_page_config(page_title="台股月差值分析", layout="centered")
st.title("📈 台股每月開盤收盤差值分析")

user_input = st.text_input("請輸入股票代碼（不需輸入 .TW 或 .TWO，例如：2399）", "2399")

def try_fetch_data(code):
    for suffix in ['.TW', '.TWO']:
        symbol = code + suffix
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max", auto_adjust=True)
        if not df.empty:
            return symbol, df, ticker
    return None, None, None

if st.button("查詢"):
    if not user_input.strip().isdigit():
        st.warning("請輸入正確的台股代碼（純數字，例如：2399）")
    else:
        with st.spinner("📡 資料載入中..."):
            stock_code, df, ticker = try_fetch_data(user_input.strip())

            if df is None:
                st.error("❌ 查無此股票，請確認代碼是否正確。")
            else:
                # 嘗試抓即時股價
                try:
                    live_price = ticker.fast_info['lastPrice']
                    st.markdown(f"💹 **即時股價（{stock_code}）**：`{live_price:.2f} 元`")
                except Exception:
                    st.warning("⚠️ 無法取得即時股價")

                df.reset_index(inplace=True)
                df['Date'] = df['Date'].dt.tz_localize(None)
                df['YearMonth'] = df['Date'].dt.to_period('M')

                first_open = df.groupby('YearMonth').first()[['Date', 'Open']].rename(columns={'Date': 'Open_Date'})
                last_close = df.groupby('YearMonth').last()[['Date', 'Close']].rename(columns={'Date': 'Close_Date'})

                monthly = pd.concat([first_open, last_close], axis=1)
                monthly['Difference'] = monthly['Close'] - monthly['Open']
                monthly.reset_index(inplace=True)

                monthly['Year'] = monthly['YearMonth'].dt.year
                monthly['Month'] = monthly['YearMonth'].dt.month

                pivot_table = monthly.pivot(index='Year', columns='Month', values='Difference')

                # ➕ 加上「每月總和」列，加在最新年份底下
                latest_year = pivot_table.index.max()
                monthly_total = pivot_table.sum(axis=0).to_frame().T
                monthly_total.index = [f"總和"]
                pivot_table = pd.concat([pivot_table, monthly_total])

                st.success(f"✅ 成功抓取：{stock_code}")
                styled = pivot_table.style.applymap(highlight_diff).format("{:.2f}")
                st.markdown("### 📊 每年各月份差值（含每月加總）")
                st.dataframe(styled, height=650)
