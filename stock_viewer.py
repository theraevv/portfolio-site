import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date, timedelta


# =========================
# PAGE CONFIG
# =========================

def configure_page():
    st.set_page_config(
        page_title="Stock Data Dashboard",
        page_icon="📈",
        layout="wide"
    )
    st.title("📈 Stock Data Dashboard")
    st.markdown("Fetch and visualize historical stock closing prices.")


# =========================
# SIDEBAR
# =========================

def render_sidebar():
    st.sidebar.header("⚙️ Settings")

    tickers_input = st.sidebar.text_input(
        "Stock Tickers (comma separated)",
        value="AAPL, MSFT, GOOGL",
        help="Enter ticker symbols separated by commas, e.g. AAPL, TSLA, NVDA"
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=date.today() - timedelta(days=365),
            max_value=date.today()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=date.today(),
            max_value=date.today()
        )

    fetch_btn = st.sidebar.button("🔍 Fetch Data", use_container_width=True)

    return tickers_input, start_date, end_date, fetch_btn


def validate_dates(start_date, end_date):
    if start_date >= end_date:
        st.sidebar.error("⚠️ Start date must be before end date.")
        st.stop()


def parse_tickers(tickers_input):
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    if not tickers:
        st.error("Please enter at least one ticker symbol.")
        st.stop()
    return tickers


# =========================
# DATA FETCHING
# =========================

@st.cache_data(show_spinner=False)
def get_data(tickers, start_date, end_date):
    all_data = []
    errors = []

    for ticker in tickers:
        df = yf.download(
            ticker,
            start=str(start_date),
            end=str(end_date),
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            errors.append(ticker)
            continue

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        if 'Close' not in df.columns:
            errors.append(ticker)
            continue

        df['Ticker'] = ticker
        df['Price'] = pd.to_numeric(df['Close'], errors='coerce')
        df = df[['Date', 'Ticker', 'Price']]
        all_data.append(df)

    if not all_data:
        return None, errors

    final_df = pd.concat(all_data, ignore_index=True)
    final_df['Date'] = pd.to_datetime(final_df['Date'])
    final_df['Price'] = pd.to_numeric(final_df['Price'], errors='coerce')
    final_df = final_df.sort_values(by='Date')

    return final_df, errors


# =========================
# DASHBOARD SECTIONS
# =========================

def render_metrics(stock_data):
    st.subheader("📊 Summary")
    metric_cols = st.columns(len(stock_data['Ticker'].unique()))

    for i, ticker in enumerate(stock_data['Ticker'].unique()):
        ticker_df = stock_data[stock_data['Ticker'] == ticker]
        latest_price = ticker_df['Price'].iloc[-1]
        first_price = ticker_df['Price'].iloc[0]
        change_pct = ((latest_price - first_price) / first_price) * 100

        with metric_cols[i]:
            st.metric(
                label=ticker,
                value=f"${latest_price:.2f}",
                delta=f"{change_pct:+.2f}% over period"
            )

    st.divider()


def render_chart(stock_data, start_date, end_date):
    st.subheader("📉 Closing Prices Over Time")

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.lineplot(
        data=stock_data,
        x='Date',
        y='Price',
        hue='Ticker',
        ax=ax,
        linewidth=2
    )
    ax.set_title(
        f"Stock Closing Prices: {start_date} → {end_date}",
        fontsize=14,
        fontweight='bold'
    )
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Closing Price (USD)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(title='Ticker', fontsize=10)
    plt.xticks(rotation=45)
    plt.tight_layout()

    st.pyplot(fig)
    st.divider()


def render_data_table(stock_data, start_date, end_date):
    st.subheader("🗂️ Raw Data")

    ticker_filter = st.multiselect(
        "Filter by Ticker",
        options=stock_data['Ticker'].unique().tolist(),
        default=stock_data['Ticker'].unique().tolist()
    )

    filtered_df = stock_data[stock_data['Ticker'].isin(ticker_filter)].copy()
    filtered_df['Date'] = filtered_df['Date'].dt.strftime('%Y-%m-%d')
    filtered_df['Price'] = filtered_df['Price'].round(2)

    st.dataframe(
        filtered_df.reset_index(drop=True),
        use_container_width=True,
        height=300
    )

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"stock_data_{start_date}_{end_date}.csv",
        mime='text/csv'
    )


# =========================
# MAIN
# =========================

def main():
    configure_page()

    tickers_input, start_date, end_date, fetch_btn = render_sidebar()
    validate_dates(start_date, end_date)

    if not fetch_btn:
        st.info("👈 Configure your settings in the sidebar and click **Fetch Data** to get started.")
        return

    tickers = parse_tickers(tickers_input)

    with st.spinner("Fetching stock data..."):
        stock_data, errors = get_data(tuple(tickers), start_date, end_date)

    if errors:
        st.warning(f"⚠️ No data found for: {', '.join(errors)}")

    if stock_data is None:
        st.error("No data could be retrieved. Please check your tickers and date range.")
        return

    render_metrics(stock_data)
    render_chart(stock_data, start_date, end_date)
    render_data_table(stock_data, start_date, end_date)


if __name__ == "__main__":
    main()
