import pandas as pd
from datetime import datetime
import streamlit as st
from streamlit_gsheets import GSheetsConnection

def get_conn():
    # Ensure it looks for 'gsheets' connection as defined in secrets
    return st.connection("gsheets", type="gsheets")

def load_data(table_name):
    """Load data directly from the specific Google Sheet tab."""
    conn = get_conn()
    df = conn.read(worksheet=table_name)
    
    # Drop empty rows that Google Sheets might accidentally return
    df = df.dropna(how='all')
    
    # Ensure proper data types
    if table_name == 'drinks' and not df.empty:
        df['cafe_id'] = df['cafe_id'].astype(str)
        
    return df

def save_data(df, table_name):
    """Overwrite the specific Google Sheet tab with the updated DataFrame."""
    conn = get_conn()
    conn.update(worksheet=table_name, data=df)

def date_to_era(date_obj):
    """Convert a datetime/date object to era_time format (YYMM integer)."""
    return int(date_obj.strftime("%y%m"))

def get_active_menu(df_drinks, cafe_name, session_date):
    """Get the latest prices for drinks valid as of the given date."""
    if df_drinks.empty:
        return pd.DataFrame()
        
    target_era = date_to_era(session_date)
    cafe_df = df_drinks[df_drinks['cafe_name'] == cafe_name].copy()
    
    if cafe_df.empty:
        return pd.DataFrame()
        
    cafe_df['era_time'] = cafe_df['era_time'].astype(int)
    valid_drinks = cafe_df[cafe_df['era_time'] <= target_era]
    
    latest_menu = valid_drinks.sort_values('era_time', ascending=False).drop_duplicates(subset=['drink'])
    return latest_menu

def generate_new_friend_id(df_friends):
    """Auto-generate a new friend ID."""
    if df_friends.empty: return 1001
    return int(df_friends['id'].max()) + 1

def generate_new_cafe_id(df_drinks):
    """Auto-generate a new cafe ID (e.g., c04)."""
    if df_drinks.empty: return "c01"
    existing_ids = df_drinks['cafe_id'].str.extract(r'(\d+)').astype(int)
    new_num = int(existing_ids.max().iloc[0]) + 1
    return f"c{new_num:02d}"
