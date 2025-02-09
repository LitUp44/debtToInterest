import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

# Function to calculate debt payback date and principal vs interest breakdown
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
    
    payback_date = start_date + pd.DateOffset(months=months)
    return payback_date, total_principal, total_interest, months

# Function to calculate future value of investment/savings
def calculate_investment_value(starting_amount, expected_return, monthly_payment, years=5):
    months = years * 12
    monthly_rate = expected_return / 12 / 100
    future_value = starting_amount
    for _ in range(months):
        future_value *= (1 + monthly_rate)
        future_value += monthly_payment
    
    total_contributions = monthly_payment * months + starting_amount
    return future_value, future_value - total_contributions

# Title and instructions
st.title("Debt to Investment/Saving Calculator")
st.markdown("""
This tool will help you determine the optimal payment strategy for your debt and investment savings. You can input as many debts and investments as you like, and then adjust the balance between debt repayment and savings to see the impact over time.
""")

# Debt Inputs
st.header("Debt Inputs")
debt_list = []
num_debts = st.number_input("How many debts do you want to enter?", min_value=1, max_value=10, value=1)

for i in range(num_debts):
    st.subheader(f"Debt {i+1}")
    amount = st.number_input(f"Amount for Debt {i+1}", min_value=0.0, value=1000.0, step=100.0)
    interest_rate = st.number_input(f"Interest Rate for Debt {i+1} (%)", min_value=0.0, value=5.0)
    start_date = st.date_input(f"Payment Start Date for Debt {i+1}", value=datetime.today())
    min_payment = st.number_input(f"Minimum Payment for Debt {i+1}", min_value=0.0, value=50.0, step=10.0)
    
    debt_list.append((amount, interest_rate, start_date, min_payment))

# Calculate Debt Results
debt_results = []
for debt in debt_list:
    payback_date, total_principal, total_interest, months = calculate_debt_payback(*debt)
    debt_results.append({
        "Payback Date": payback_date,
        "Principal Paid": total_principal,
        "Interest Paid": total_interest,
        "Months to Pay Off": months
    })

debt_df = pd.DataFrame(debt_results)
st.write(debt_df)

# Investment Inputs
st.header("Investment / Savings Inputs")
investment_list = []
num_investments = st.number_input("How many investments do you want to enter?", min_value=1, max_value=10, value=1)

for i in range(num_investments):
    st.subheader(f"Investment {i+1}")
    starting_amount = st.number_input(f"Starting Amount for Investment {i+1}", min_value=0.0, value=1000.0, step=100.0)
    expected_return = st.number_input(f"Expected Return for Investment {i+1} (%)", min_value=0.0, value=6.0)
    monthly_payment = st.number_input(f"Monthly Payment for Investment {i+1}", min_value=0.0, value=100.0, step=10.0)
    
    investment_list.append((starting_amount, expected_return, monthly_payment))

# Calculate Investment Results
investment_results = []
for investment in investment_list:
    future_value, return_amount = calculate_investment_value(*investment)
    investment_results.append({
        "Future Value after 5 Years": future_value,
        "Total Contributions": investment[0] + investment[2] * 12 * 5,
        "Return after 5 Years": return_amount
    })

investment_df = pd.DataFrame(investment_results)
st.write(investment_df)

# Interactive Slider for Adjusting Money Between Debt and Investment
st.header("Adjust Payment Strategy Between Debt and Investment")
total_income = st.number_input("Total Available Monthly Payment", min_value=0.0, value=500.0, step=10.0)

# Slider to allocate funds
debt_percentage = st.slider("Percentage of Available Funds to Allocate to Debt", min_value=0, max_value=100, value=50)
investment_percentage = 100 - debt_percentage

debt_payment = total_income * (debt_percentage / 100)
investment_payment = total_income * (investment_percentage / 100)

st.write(f"Debt Allocation: ${debt_payment:.2f} per month")
st.write(f"Investment Allocation: ${investment_payment:.2f} per month")

# Recalculate results based on new allocations (you could adjust this logic depending on how you'd like to handle payments)
debt_payment_updated = st.number_input("Updated Debt Payment", value=debt_payment)
investment_payment_updated = st.number_input("Updated Investment Payment", value=investment_payment)

st.write(f"Updated Debt Payment: ${debt_payment_updated:.2f}")
st.write(f"Updated Investment Payment: ${investment_payment_updated:.2f}")

# Add more advanced calculations as needed

