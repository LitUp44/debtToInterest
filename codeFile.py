import streamlit as st
import pandas as pd  # Global import
from datetime import datetime
import numpy as np

# Cache expensive functions to optimize startup time
@st.cache
def calculate_debt_payback(principal, interest_rate, start_date, min_payment):
    monthly_rate = interest_rate / 12 / 100
    months = 0
    total_interest = 0
    total_principal = 0
    remaining_balance = principal
    
    while remaining_balance > 0:
        interest_payment = remaining_balance * monthly_rate
        principal_payment = min_payment - interest_payment
        remaining_balance -= principal_payment
        total_interest += interest_payment
        total_principal += principal_payment
        months += 1
    
    years = months / 12
    payback_date = start_date + pd.DateOffset(months=months)
    return payback_date, total_principal, total_interest, years

@st.cache
def calculate_investment_value(starting_amount, expected_return, monthly_payment, years=5):
    months = years * 12
    monthly_rate = expected_return / 12 / 100
    future_value = starting_amount
    for _ in range(months):
        future_value *= (1 + monthly_rate)
        future_value += monthly_payment
    
    total_contributions = monthly_payment * months + starting_amount
    return future_value, future_value - total_contributions

# Initialize session state for debts and investments (only store essential data)
if 'debt_list' not in st.session_state:
    st.session_state.debt_list = []

if 'investment_list' not in st.session_state:
    st.session_state.investment_list = []

# Title and instructions
st.title("Debt to Investment/Saving Calculator")
st.markdown("""
This tool will help you determine the optimal payment strategy for your debt and investment savings. 
You can input as many debts and investments as you like, and then adjust the balance between debt repayment 
and savings to see the impact over time.
""")

# Side panel for adding new debts and investments
with st.sidebar:
    st.header("Add New Debt")
    if st.button("Add New Debt"):
        amount = st.number_input("Debt Amount", min_value=0.0, value=1000.0, step=100.0)
        interest_rate = st.number_input("Interest Rate for Debt (%)", min_value=0.0, value=5.0)
        start_date = st.date_input("Payment Start Date for Debt", value=datetime.today())
        min_payment = st.number_input("Minimum Payment for Debt", min_value=0.0, value=50.0, step=10.0)
        
        # Add to session state only if valid input
        if amount > 0 and min_payment > 0:
            st.session_state.debt_list.append((amount, interest_rate, start_date, min_payment))

    st.header("Add New Investment")
    if st.button("Add New Investment"):
        starting_amount = st.number_input("Starting Amount for Investment", min_value=0.0, value=1000.0, step=100.0)
        expected_return = st.number_input("Expected Return for Investment (%)", min_value=0.0, value=6.0)
        monthly_payment = st.number_input("Monthly Payment for Investment", min_value=0.0, value=100.0, step=10.0)
        
        # Add to session state only if valid input
        if starting_amount > 0 and monthly_payment > 0:
            st.session_state.investment_list.append((starting_amount, expected_return, monthly_payment))

# Step 2: Show Debts and Investments Tables with Updated Payments
st.header("Debts")
debt_results = []
for i, debt in enumerate(st.session_state.debt_list):
    payback_date, total_principal, total_interest, years = calculate_debt_payback(*debt)
    debt_results.append({
        "Debt Amount": debt[0],
        "Recommended Payment": debt[3],  # Monthly minimum payment
        "Payback Date": payback_date,
        "Interest Paid": total_interest,
        "Years to Pay Off": years,
        "Actions": f"Edit/Delete {i+1}"  # Add Edit/Delete button text
    })

# Display the table
debt_df = pd.DataFrame(debt_results)
st.write(debt_df)

# Edit/Delete functionality for debts
for i, debt in enumerate(st.session_state.debt_list):
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"Edit Debt {i+1}"):
            new_amount = st.number_input(f"New Amount for Debt {i+1}", value=debt[0])
            new_interest_rate = st.number_input(f"New Interest Rate for Debt {i+1} (%)", value=debt[1])
            new_min_payment = st.number_input(f"New Minimum Payment for Debt {i+1}", value=debt[3])
            new_start_date = st.date_input(f"New Payment Start Date for Debt {i+1}", value=debt[2])
            
            if new_amount > 0 and new_min_payment > 0:
                st.session_state.debt_list[i] = (new_amount, new_interest_rate, new_start_date, new_min_payment)
                st.success(f"Debt {i+1} updated successfully!")

    with col2:
        if st.button(f"Delete Debt {i+1}"):
            del st.session_state.debt_list[i]
            st.success(f"Debt {i+1} deleted successfully!")
            break  # Break to re-render after deleting

st.header("Investments/Savings")
investment_results = []
for i, investment in enumerate(st.session_state.investment_list):
    future_value, return_amount = calculate_investment_value(*investment)
    investment_results.append({
        "Investment Amount": investment[0],
        "Total Contributions": investment[0] + investment[2] * 12 * 5,
        "Future Value": future_value,
        "Return After 5 Years": return_amount,
        "Actions": f"Edit/Delete {i+1}"  # Add Edit/Delete button text
    })

# Display the table
investment_df = pd.DataFrame(investment_results)
st.write(investment_df)

# Edit/Delete functionality for investments
for i, investment in enumerate(st.session_state.investment_list):
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"Edit Investment {i+1}"):
            new_starting_amount = st.number_input(f"New Starting Amount for Investment {i+1}", value=investment[0])
            new_expected_return = st.number_input(f"New Expected Return for Investment {i+1} (%)", value=investment[1])
            new_monthly_payment = st.number_input(f"New Monthly Payment for Investment {i+1}", value=investment[2])
            
            if new_starting_amount > 0 and new_monthly_payment > 0:
                st.session_state.investment_list[i] = (new_starting_amount, new_expected_return, new_monthly_payment)
                st.success(f"Investment {i+1} updated successfully!")

    with col2:
        if st.button(f"Delete Investment {i+1}"):
            del st.session_state.investment_list[i]
            st.success(f"Investment {i+1} deleted successfully!")
            break  # Break to re-render after deleting

# Future Value calculation remains the same...

