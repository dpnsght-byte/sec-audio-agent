import streamlit as st
import sqlite3
import pandas as pd

# --- BRANDING ---
st.set_page_config(page_title="Deep Insights - Admin Dashboard", layout="centered")
st.title("🎙️ Deep Insights")
st.subheader("SEC Edgar AI Monitoring Agent - Admin Panel")

# --- DATABASE SETUP ---
DB_NAME = "tickers.db"

def init_db():
    """Initialize the SQLite database to store tickers."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_companies (
            ticker TEXT PRIMARY KEY,
            added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_ticker(ticker):
    """Add a new ticker to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Convert to uppercase for consistency
        cursor.execute("INSERT INTO tracked_companies (ticker) VALUES (?)", (ticker.upper(),))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False # Ticker already exists
    conn.close()
    return success

def get_tickers():
    """Retrieve all tracked tickers."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT ticker, added_on FROM tracked_companies ORDER BY added_on DESC", conn)
    conn.close()
    return df

def delete_ticker(ticker):
    """Remove a ticker from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracked_companies WHERE ticker = ?", (ticker,))
    conn.commit()
    conn.close()

# Initialize Database on startup
init_db()

# --- DASHBOARD UI ---

st.markdown("Enter the stock tickers of the companies you want the AI agent to monitor 24/7 for new 10-K and 10-Q filings.")

# Section 1: Add a Ticker
with st.form("add_ticker_form", clear_on_submit=True):
    new_ticker = st.text_input("Enter Company Ticker (e.g., AAPL, TSLA, MSFT):")
    submitted = st.form_submit_button("Add to Tracking List")

    if submitted:
        if new_ticker.strip():
            if add_ticker(new_ticker.strip()):
                st.success(f"✅ Successfully added {new_ticker.upper()} to the monitoring list!")
            else:
                st.warning(f"⚠️ {new_ticker.upper()} is already being tracked.")
        else:
            st.error("Please enter a valid ticker.")

# Section 2: View and Manage Tracked Tickers
st.divider()
st.subheader("Currently Tracked Companies")

tickers_df = get_tickers()

if tickers_df.empty:
    st.info("No companies are currently being tracked. Add a ticker above to get started.")
else:
    # Display the list of tracked companies
    st.dataframe(tickers_df, use_container_width=True, hide_index=True)
    
    # Delete functionality
    st.markdown("### Remove a Ticker")
    ticker_to_delete = st.selectbox("Select a ticker to stop tracking:", tickers_df['ticker'].tolist())
    if st.button("Stop Tracking"):
        delete_ticker(ticker_to_delete)
        st.success(f"🛑 Stopped tracking {ticker_to_delete}.")
        st.rerun() # Refresh the page to update the table
