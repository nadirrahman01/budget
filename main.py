import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, auth
import altair as alt
from streamlit import session_state as session
import requests
from datetime import datetime

# Import Firebase configuration
from firebase_config import firebaseConfig

# Firebase API Key
FIREBASE_API_KEY = "AIzaSyDjcAK9YkvLQJGrtKSeO6RDOq_gByfwZiI"

# Initialize Firebase app if it is not already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("config/budget-51277-firebase-adminsdk-alcjk-c2cd65f747.json")
    firebase_admin.initialize_app(cred)

# Initialize session state for user information and data (replace with a database in production)
if 'users_db' not in session:
    session['users_db'] = {}

if 'user_data_db' not in session:
    session['user_data_db'] = {}

def user_authentication():
    st.sidebar.title("User Authentication")
    choice = st.sidebar.selectbox('Login/Signup', ['Login', 'Signup'])
    email = st.sidebar.text_input('Email')
    password = st.sidebar.text_input('Password', type='password')

    if choice == 'Signup':
        submit = st.sidebar.button('Create my account')
        if submit:
            try:
                user = auth.create_user(email=email, password=password)
                session['users_db'][user.uid] = {"email": email, "password": password}
                session['user_data_db'][user.uid] = {
                    "budget": {},
                    "savings_goals": [],
                    "investments": []
                }
                st.success('Your account is created successfully')
                st.info('Please login to continue.')
            except Exception as e:
                st.error(f"Error: {e}")

    if choice == 'Login':
        login = st.sidebar.button('Login')
        if login:
            try:
                payload = {
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
                r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}", json=payload)
                if r.status_code == 200:
                    user_data = r.json()
                    user_uid = user_data['localId']
                    session['user'] = user_uid
                    if user_uid not in session['user_data_db']:
                        session['user_data_db'][user_uid] = {
                            "budget": {},
                            "savings_goals": [],
                            "investments": []
                        }
                    st.sidebar.success('Login successful')
                    st.experimental_rerun()
                else:
                    st.error("Invalid email or password.")
            except Exception as e:
                st.error(f"Error: {e}")

def user_logout():
    if st.sidebar.button('Logout'):
        session.clear()
        st.experimental_rerun()

def display_kpi(title, value):
    st.markdown(
        f"""
        <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #333;">{title}</h4>
            <h2 style="margin: 0; color: #007BFF;">{value}</h2>
        </div>
        """, unsafe_allow_html=True)

def dashboard_overview():
    st.markdown("# Dashboard Overview")
    user_uid = session['user']
    st.markdown(f"### Summary of your budget, expenses, savings, and investments for user {user_uid}.")

    if user_uid in session['user_data_db']:
        user_data = session['user_data_db'][user_uid]
        budget_data = pd.DataFrame(list(user_data["budget"].items()), columns=["Category", "Budget"])
        savings_data = pd.DataFrame(user_data["savings_goals"]) if user_data["savings_goals"] else pd.DataFrame(columns=["goal", "amount"])
        investment_data = pd.DataFrame(user_data["investments"]) if user_data["investments"] else pd.DataFrame(columns=["investment", "amount"])
    else:
        st.error("User data not found.")
        return

    st.markdown("## Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    with col1:
        display_kpi("Total Budget", f"${budget_data['Budget'].sum()}")
    with col2:
        display_kpi("Total Savings Goals", f"${savings_data['amount'].sum()}")
    with col3:
        display_kpi("Total Investments", f"${investment_data['amount'].sum()}")

    st.markdown("## Budget Allocation")
    pie_chart = alt.Chart(budget_data).mark_arc(innerRadius=50).encode(
        theta=alt.Theta(field="Budget", type="quantitative"),
        color=alt.Color(field="Category", type="nominal"),
        tooltip=["Category", "Budget"]
    ).properties(
        title="Budget Allocation"
    )
    st.altair_chart(pie_chart, use_container_width=True)

    st.markdown("## Savings Goals")
    if not savings_data.empty:
        st.dataframe(savings_data)
    else:
        st.write("No savings goals set.")

    st.markdown("## Investments")
    if not investment_data.empty:
        st.dataframe(investment_data)
    else:
        st.write("No investments made.")

def budget_allocation():
    st.markdown("## Budget Allocation")
    st.write("Allocate your budget to different categories.")
    user_uid = session['user']
    categories = ["Groceries", "Entertainment", "Utilities", "Transport", "Miscellaneous"]

    allocation = {category: st.number_input(f"Budget for {category}", min_value=0) for category in categories}

    if st.button("Save Allocation"):
        session['user_data_db'][user_uid]["budget"] = allocation
        st.success("Allocation saved!")
        st.write(pd.DataFrame.from_dict(allocation, orient='index', columns=['Amount']))

def savings_goals():
    st.markdown("## Savings Goals")
    st.write("Create and manage your savings goals.")
    user_uid = session['user']
    goal = st.text_input("Goal Name")
    amount = st.number_input("Goal Amount", min_value=0)

    if st.button("Add Goal"):
        if goal and amount > 0:
            session['user_data_db'][user_uid]["savings_goals"].append({"goal": goal, "amount": amount})
            st.success(f"Goal '{goal}' with amount {amount} added.")
            st.write(pd.DataFrame(session['user_data_db'][user_uid]["savings_goals"]))
        else:
            st.error("Please enter a valid goal name and amount.")

def investment_tracker():
    st.markdown("## Investment Tracker")
    st.write("Track your investments.")
    user_uid = session['user']
    investment = st.text_input("Investment Name")
    amount = st.number_input("Investment Amount", min_value=0)

    if st.button("Add Investment"):
        if investment and amount > 0:
            session['user_data_db'][user_uid]["investments"].append({"investment": investment, "amount": amount})
            st.success(f"Investment '{investment}' with amount {amount} added.")
            st.write(pd.DataFrame(session['user_data_db'][user_uid]["investments"]))
        else:
            st.error("Please enter a valid investment name and amount.")

def market_research():
    st.markdown("## Market Research and Recommendations")
    st.write("Conduct market research and get financial advice.")
    user_uid = session['user']

    st.write("Fetching real-time market data...")
    st.write(pd.DataFrame({
        'Stock': ['AAPL', 'GOOGL', 'AMZN', 'MSFT'],
        'Price': [150, 2800, 3400, 300]
    }))

def main():
    st.sidebar.title("Navigation")
    if 'user' not in session:
        user_authentication()
    else:
        user_logout()
        options = st.sidebar.radio("Go to", ["Dashboard", "Budget Allocation", "Savings Goals", "Investment Tracker", "Market Research"])

        if options == "Dashboard":
            dashboard_overview()
        elif options == "Budget Allocation":
            budget_allocation()
        elif options == "Savings Goals":
            savings_goals()
        elif options == "Investment Tracker":
            investment_tracker()
        elif options == "Market Research":
            market_research()

if __name__ == "__main__":
    main()