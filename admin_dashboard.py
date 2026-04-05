import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text

# --- BRANDING ---
st.set_page_config(page_title="Deep Insights - Admin Dashboard", layout="centered")
st.title("🎙️ Deep Insights")
st.subheader("SEC Edgar AI Monitoring Agent - Admin Panel")

# --- DATABASE SETUP ---
# Get the Database URL from Render, or use local SQLite if testing locally
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # SQLAlchemy requires postgresql:// instead of postgres://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL)
else:
    # Fallback for local testing
    engine = create_engine("sqlite:///tickers.db")

def init_db():
    """Initialize the database table."""
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS tracked_companies (
                ticker VARCHAR(10) PRIMARY KEY,
                added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''))
        conn.commit()

def add_ticker(ticker):
    """Add a new ticker to the database."""
    ticker = ticker.upper().strip()
    try:
        with engine.connect() as conn:
            # Check if it already exists
            result = conn.execute(text("SELECT 1 FROM tracked_companies WHERE ticker = :t"), {"t": ticker}).fetchone()
            if result:
                return False # Already exists
            
            # Insert the new ticker
            conn.execute(text("INSERT INTO tracked_companies (ticker) VALUES (:t)"), {"t": ticker})
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def get_tickers():
    """Retrieve all tracked tickers."""
    try:
        df = pd.read_sql_query("SELECT ticker, added_on FROM tracked_companies ORDER BY added_on DESC", engine)
        return df
    except Exception:
        return pd.DataFrame(columns=['ticker', 'added_on'])

def delete_ticker(ticker):
    """Remove a ticker from the database."""
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM tracked_companies WHERE ticker = :t"), {"t": ticker})
        conn.commit()

# Initialize Database on startup
init_db()

# --- DASHBOARD UI ---
st.markdown("Enter the stock tickers of the companies you want the AI agent to monitor 24/7.")

# Section 1: Add a Ticker
with st.form("add_ticker_form", clear_on_submit=True):
    new_ticker = st.text_input("Enter Company Ticker (e.g., AAPL, TSLA):")
    submitted = st.form_submit_button("Add to Tracking List")

    if submitted:
        if new_ticker:
            if add_ticker(new_ticker):
                st.success(f"✅ Successfully added {new_ticker.upper()}!")
            else:
                st.warning(f"⚠️ {new_ticker.upper()} is already being tracked.")
        else:
            st.error("Please enter a valid ticker.")

# Section 2: View and Manage
st.divider()
st.subheader("Currently Tracked Companies")

tickers_df = get_tickers()

if tickers_df.empty:
    st.info("No companies are currently being tracked.")
else:
    st.dataframe(tickers_df, use_container_width=True, hide_index=True)
    
    st.markdown("### Remove a Ticker")
    ticker_to_delete = st.selectbox("Select a ticker to stop tracking:", tickers_df['ticker'].tolist())
    if st.button("Stop Tracking"):
        delete_ticker(ticker_to_delete)
        st.success(f"🛑 Stopped tracking {ticker_to_delete}.")
        st.rerun()
