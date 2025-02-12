import streamlit as st
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
This tool will help you determine the optimal payment strategy for your debt and investment savings. You can input as many debts and investments as you like, and then adjust the balance between debt repayment and savings to see the impact over time.
""")

# Step 1: Side panel for debt and investment entry
with st.sidebar:
    st.header("Add New Debt")
    if st.button("Add New Debt"):
        amount = st.number_input(f"Debt Amount", min_value=0.0, value=1000.0, step=100.0)
        interest_rate = st.number_input(f"Interest Rate for Debt (%)", min_value=0.0, value=5.0)
        start_date = st.date_input(f"Payment Start Date for Debt", value=datetime.today())
        min_payment = st.number_input(f"Minimum Payment for Debt", min_value=0.0, value=50.0, step=10.0)
        
        # Add to session state only if valid input
        if amount > 0 and min_payment > 0:
            st.session_state.debt_list.append((amount, interest_rate, start_date, min_payment))

    st.header("Add New Investment")
    if st.button("Add New Investment"):
        starting_amount = st.number_input(f"Starting Amount for Investment", min_value=0.0, value=1000.0, step=100.0)
        expected_return = st.number_input(f"Expected Return for Investment (%)", min_value=0.0, value=6.0)
        monthly_payment = st.number_input(f"Monthly Payment for Investment", min_value=0.0, value=100.0, step=10.0)
        
        # Add to session state only if valid input
        if starting_amount > 0 and monthly_payment > 0:
            st.session_state.investment_list.append((starting_amount, expected_return, monthly_payment))

# Step 2: Show Debts and Investments Tables with Updated Payments
st.header("Debts")
debt_results = []
for debt in st.session_state.debt_list:
    payback_date, total_principal, total_interest, years = calculate_debt_payback(*debt)
    debt_results.append({
        "Debt Amount": debt[0],
        "Recommended Payment": debt[3],  # Monthly minimum payment
        "Payback Date": payback_date,
        "Interest Paid": total_interest,
        "Years to Pay Off": years
    })

debt_df = pd.DataFrame(debt_results)
st.write(debt_df)

# Add editable payments to each debt
st.header("Edit Monthly Payments for Debts")
for i, debt in enumerate(st.session_state.debt_list):
    debt_payment = st.number_input(f"Debt {i+1} Monthly Contribution", min_value=0.0, value=debt[3], step=10.0)
    st.session_state.debt_list[i] = (debt[0], debt[1], debt[2], debt_payment)  # Update with new value

st.header("Investments/Savings")
investment_results = []
for investment in st.session_state.investment_list:
    future_value, return_amount = calculate_investment_value(*investment)
    investment_results.append({
        "Investment Amount": investment[0],
        "Total Contributions": investment[0] + investment[2] * 12 * 5,
        "Future Value": future_value,
        "Return After 5 Years": return_amount
    })

investment_df = pd.DataFrame(investment_results)
st.write(investment_df)

# Add editable payments to each investment
st.header("Edit Monthly Contributions for Investments")
for i, investment in enumerate(st.session_state.investment_list):
    investment_payment = st.number_input(f"Investment {i+1} Monthly Contribution", min_value=0.0, value=investment[2], step=10.0)
    st.session_state.investment_list[i] = (investment[0], investment[1], investment_payment)  # Update with new value

# Step 3: Future Value Calculation (Combining Investments and Debts)
st.header("Future Value Calculation")
future_years = st.number_input("Enter number of years for future value calculation", min_value=1, value=5)
total_debt = sum([debt[0] for debt in st.session_state.debt_list])  # Sum of all debt amounts
total_investment = sum([investment[0] for investment in st.session_state.investment_list])  # Sum of all investment amounts

# Calculate combined future value (investment - debt)
combined_future_value = 0
for debt in st.session_state.debt_list:
    payback_date, total_principal, total_interest, years = calculate_debt_payback(*debt)
    total_debt -= total_principal  # Debt decreases as payments are made

for investment in st.session_state.investment_list:
    future_value, return_amount = calculate_investment_value(*investment, years=future_years)
    combined_future_value += future_value

combined_future_value -= total_debt  # Subtract debt from the combined future value

st.write(f"Combined Future Value (Investments - Debts) after {future_years} years: ${combined_future_value:.2f}")


