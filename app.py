import streamlit as st
import pandas as pd
from datetime import datetime
import db_manager as db

import streamlit as st
# Test if secrets are loaded
try:
    st.write("Is GSheets connected?", st.connection("gsheets") is not None)
except Exception as e:
    st.error(f"Error loading secrets: {e}")

# Page configuration and RTL layout setup for Arabic UI
st.set_page_config(page_title="Cafe Management System", page_icon="☕", layout="wide")
st.markdown("""
    <style>
    body, [class*="css"], .stApp { direction: rtl; text-align: right; }
    .stTabs [data-baseweb="tab-list"] { direction: rtl; }
    div[data-testid="column"] { display: flex; flex-direction: column; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# Load all dataframes from Google Sheets into memory
df_friends = db.load_data('friends')
df_drinks = db.load_data('drinks')
df_history = db.load_data('history')

# Initialize session state for current table orders
if "current_orders" not in st.session_state:
    st.session_state.current_orders = []

st.title("☕ منظومة إدارة مشاريب الشلة")

# ==================== ADMIN SECURITY SYSTEM ====================
st.sidebar.title("🔒 الإدارة والصلاحيات")

# Check if the user knows the password
admin_password = st.sidebar.text_input("كلمة مرور الإدارة (Password)", type="password", help="أدخل كلمة المرور لتعديل المنيو والأصدقاء")

# Define the master password (you can change this to anything)
is_admin = (admin_password == "bonn2026") # <-- غير الباسورد من هنا

if is_admin:
    st.sidebar.success("تم تفعيل صلاحيات الأدمن بالكامل.")
    # Show all tabs for the Admin
    tabs = st.tabs([
        "📝 تسجيل المشاريب", 
        "📊 السجل التاريخي", 
        "👥 إدارة الشلة", 
        "🍹 إدارة الكافيهات والمنيو"
    ])
    tab_orders, tab_history, tab_friends, tab_menu = tabs
else:
    st.sidebar.info("صلاحيات المستخدم العادي: إضافة طلبات للطرابيزة فقط.")
    # Show ONLY the ordering tab for normal users
    tabs = st.tabs(["📝 تسجيل المشاريب"])
    tab_orders = tabs[0]

# ==================== TAB 1: RECORD ORDERS (Visible to Everyone) ====================
with tab_orders:
    st.header("📍 تفاصيل القعدة")
    
    col1, col2 = st.columns(2)
    with col1: 
        session_date = st.date_input("التاريخ (Date)", datetime.today())
    with col2: 
        cafe_list = df_drinks['cafe_name'].unique().tolist() if not df_drinks.empty else []
        session_cafe = st.selectbox("المكان (Cafe Name)", cafe_list)
    
    st.markdown("---")
    
    if not cafe_list:
        st.warning("⚠️ لا يوجد كافيهات مسجلة.")
    else:
        # Fetch the menu valid ONLY for the selected date
        cafe_menu = db.get_active_menu(df_drinks, session_cafe, session_date)
        
        if cafe_menu.empty:
            st.warning(f"⚠️ لا يوجد مشاريب مسجلة في ({session_cafe}) قبل أو خلال هذا التاريخ.")
        else:
            friends_dict = {f"{r['code_name']}": r['id'] for _, r in df_friends.iterrows()}
            drinks_dict = {f"{r['drink']} ({r['price']} L.E)": r for _, r in cafe_menu.iterrows()}
            
            c1, c2, c3 = st.columns(3)
            with c1: 
                selected_friend_name = st.selectbox("الشخص (Friend)", options=list(friends_dict.keys()), index=None, placeholder="ابحث واختار الاسم...")
            with c2: 
                selected_drink_str = st.selectbox("المشروب (Drink)", options=list(drinks_dict.keys()), index=None, placeholder="ابحث واختار المشروب...")
            with c3: 
                qty = st.number_input("العدد (Qty)", min_value=1, value=1)
                
            if st.button("➕ إضافة للطرابيزة", use_container_width=True):
                if selected_friend_name and selected_drink_str:
                    drink_data = drinks_dict[selected_drink_str]
                    st.session_state.current_orders.append({
                        "date": str(session_date),
                        "cafe_name": session_cafe,
                        "friend_name": selected_friend_name,
                        "drink": drink_data['drink'],
                        "qty": qty,
                        "price": drink_data['price'],
                        "total": qty * drink_data['price']
                    })
                    st.success("تم الإضافة للطرابيزة بنجاح!")
                    st.rerun()
                else:
                    st.error("⚠️ برجاء اختيار اسم الشخص والمشروب أولاً.")

    # Display current orders and inline delete buttons
    if st.session_state.current_orders:
        st.markdown("---")
        st.subheader("📋 الطلبات الحالية على الطرابيزة")
        
        h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns([2, 2, 1, 1, 1, 1])
        h_col1.markdown("**الشخص**")
        h_col2.markdown("**المشروب**")
        h_col3.markdown("**العدد**")
        h_col4.markdown("**السعر**")
        h_col5.markdown("**الإجمالي**")
        h_col6.markdown("**حذف**")
        
        st.markdown("<hr style='margin: 0.5em 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        for i, order in enumerate(st.session_state.current_orders):
            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns([2, 2, 1, 1, 1, 1])
            row_col1.write(order['friend_name'])
            row_col2.write(order['drink'])
            row_col3.write(str(order['qty']))
            row_col4.write(str(order['price']))
            row_col5.write(str(order['total']))
            
            if row_col6.button("❌", key=f"delete_order_{i}", help="حذف هذا الطلب"):
                st.session_state.current_orders.pop(i)
                st.rerun()
                
        st.markdown("---")
        df_current = pd.DataFrame(st.session_state.current_orders)
        
        total_bill = df_current["total"].sum() if not df_current.empty else 0
        st.info(f"**إجمالي الحساب: {total_bill} L.E**")
        
        if not df_current.empty:
            if st.button("💾 حفظ وترحيل البيانات", type="primary", use_container_width=True):
                # Update Google Sheets History directly
                df_updated = pd.concat([df_history, df_current], ignore_index=True)
                db.save_data(df_updated, 'history')
                st.session_state.current_orders = []
                st.success("تم الحفظ بنجاح في قاعدة البيانات!")
                st.rerun()

# ==================== ADMIN ONLY TABS ====================
if is_admin:
    
    with tab_history:
        st.header("📊 السجل التاريخي (History)")
        st.dataframe(df_history, use_container_width=True)

    with tab_friends:
        st.header("👥 إضافة أعضاء الشلة")
        st.dataframe(df_friends, use_container_width=True)
        
        with st.form("add_friend_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1: new_code_name = st.text_input("الاسم الحركي (code_name)")
            with col_f2: new_birthday = st.text_input("تاريخ الميلاد (مثال: 15-9-96)")
                
            if st.form_submit_button("حفظ الصديق الجديد") and new_code_name:
                new_id = db.generate_new_friend_id(df_friends)
                new_row = pd.DataFrame({"id": [new_id], "code_name": [new_code_name], "birthday": [new_birthday]})
                df_friends = pd.concat([df_friends, new_row], ignore_index=True)
                db.save_data(df_friends, 'friends')
                st.success("تمت الإضافة بنجاح لجوجل شيت!")
                st.rerun()

    with tab_menu:
        st.header("🍹 إضافة وتحديث الأسعار والمشروبات")
        st.dataframe(df_drinks, use_container_width=True)
        
        is_new_cafe = st.checkbox("تسجيل كافيه جديد (Create New Cafe)")
        
        with st.form("add_drink_form"):
            col_m1, col_m2 = st.columns(2)
            
            with col_m1:
                if is_new_cafe:
                    input_cafe_name = st.text_input("اسم الكافيه الجديد (New cafe_name)")
                else:
                    existing_cafes = df_drinks['cafe_name'].unique().tolist() if not df_drinks.empty else []
                    input_cafe_name = st.selectbox("اختر الكافيه (Select Cafe)", existing_cafes)
                    
                input_drink = st.text_input("اسم المشروب (drink)")
                
            with col_m2:
                input_price = st.number_input("السعر (price)", min_value=1)
                effective_date = st.date_input("تاريخ تفعيل السعر (Effective Date)")
                target_era = db.date_to_era(effective_date)
                st.text_input("الفترة الزمنية المحسوبة (era_time)", value=str(target_era), disabled=True)
                
            submit_drink = st.form_submit_button("حفظ التحديث")
            
            if submit_drink and input_drink and input_cafe_name:
                if is_new_cafe:
                    target_cafe_id = db.generate_new_cafe_id(df_drinks)
                else:
                    target_cafe_id = df_drinks[df_drinks['cafe_name'] == input_cafe_name]['cafe_id'].iloc[0]
                
                mask = (df_drinks['cafe_name'] == input_cafe_name) & \
                       (df_drinks['drink'] == input_drink) & \
                       (df_drinks['era_time'].astype(int) == target_era)
                       
                if mask.any():
                    df_drinks.loc[mask, 'price'] = input_price
                else:
                    new_drink_row = pd.DataFrame({
                        "cafe_id": [target_cafe_id],
                        "cafe_name": [input_cafe_name],
                        "drink": [input_drink],
                        "price": [input_price],
                        "era_time": [target_era]
                    })
                    df_drinks = pd.concat([df_drinks, new_drink_row], ignore_index=True)
                    
                db.save_data(df_drinks, 'drinks')
                st.success("تم حفظ المشروب في جوجل شيت بنجاح!")
                st.rerun()
