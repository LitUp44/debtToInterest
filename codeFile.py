import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =============================================================================
# Helper Functions
# =============================================================================
def calculate_payoff_months(amount, annual_interest_rate, payment):
    """
    Simulate month-by-month payoff of a debt.
    Returns the number of months required to pay off the debt.
    If payment is too low to ever pay off the debt, returns None.
    """
    monthly_rate = annual_interest_rate / 100 / 12
    balance = amount
    months = 0

    # if payment does not cover the monthly interest, the balance will never decline
    if payment <= balance * monthly_rate:
        return None

    while balance > 0 and months < 1000:  # safeguard against infinite loops
        balance = balance * (1 + monthly_rate) - payment
        months += 1
    return months

def remaining_balance(amount, annual_interest_rate, payment, months):
    """
    Calculate remaining balance on a debt after a given number of months.
    If the debt is paid off before the horizon, returns 0.
    """
    monthly_rate = annual_interest_rate / 100 / 12
    balance = amount
    for m in range(months):
        if payment <= balance * monthly_rate:
            break
        balance = balance * (1 + monthly_rate) - payment
        if balance <= 0:
            return 0
    return max(balance, 0)

def future_value(current_amount, monthly_contribution, annual_return_rate, months):
    """
    Calculate the future value of an investment with monthly contributions.
    """
    r = annual_return_rate / 100 / 12
    if r != 0:
        fv = current_amount * (1 + r) ** months + monthly_contribution * (((1 + r) ** months - 1) / r)
    else:
        fv = current_amount + monthly_contribution * months
    return fv

def net_worth_over_time(debts, investments, horizon_months):
    """
    Create a DataFrame tracking net worth (investments minus remaining debt)
    for each month up to the given horizon.
    """
    months = list(range(horizon_months + 1))
    net_worth = []
    total_debt_series = []
    total_investment_series = []
    
    for m in months:
        total_debt = sum(
            remaining_balance(debt["Amount Owed"], debt["Interest Rate"], debt["Current Payment"], m)
            for debt in debts
        )
        total_investment = sum(
            future_value(inv["Current Amount"], inv["Monthly Contribution"], inv["Return Rate"], m)
            for inv in investments
        )
        net_worth.append(total_investment - total_debt)
        total_debt_series.append(total_debt)
        total_investment_series.append(total_investment)
    
    df = pd.DataFrame({
        "Month": months,
        "Net Worth": net_worth,
        "Total Debt": total_debt_series,
        "Total Investments": total_investment_series
    })
    return df

# =============================================================================
# Session State Initialization
# =============================================================================
if "debts" not in st.session_state:
    st.session_state.debts = []  # List of debt dictionaries
if "investments" not in st.session_state:
    st.session_state.investments = []  # List of investment dictionaries
if "editing_debt_index" not in st.session_state:
    st.session_state.editing_debt_index = None
if "editing_investment_index" not in st.session_state:
    st.session_state.editing_investment_index = None

# =============================================================================
# Sidebar: Debt Input / Edit Form
# =============================================================================
st.sidebar.title("Manage Your Finances")
st.sidebar.header("Debt Details")

if st.session_state.editing_debt_index is not None:
    debt_mode = "edit"
    debt_idx = st.session_state.editing_debt_index
    debt_record = st.session_state.debts[debt_idx]
    default_debt_name = debt_record["Debt Name"]
    default_amount_owed = debt_record["Amount Owed"]
    default_interest_rate = debt_record["Interest Rate"]
    default_min_payment = debt_record["Minimum Payment"]
    default_current_payment = debt_record["Current Payment"]
    debt_form_title = "Edit Debt"
    debt_submit_label = "Save Changes"
else:
    debt_mode = "add"
    default_debt_name = ""
    default_amount_owed = 0.0
    default_interest_rate = 0.0
    default_min_payment = 0.0
    default_current_payment = 0.0
    debt_form_title = "Add Debt"
    debt_submit_label = "Add Debt"

st.sidebar.subheader(debt_form_title)
with st.sidebar.form("debt_form", clear_on_submit=True):
    debt_name = st.text_input("Debt Name", value=default_debt_name, key="debt_name_input")
    amount_owed = st.number_input("Amount Owed", min_value=0.0, value=default_amount_owed, key="amount_owed_input")
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=default_interest_rate, key="interest_rate_input")
    min_payment = st.number_input("Minimum Payment", min_value=0.0, value=default_min_payment, key="min_payment_input")
    current_payment = st.number_input("Current Payment", min_value=0.0, value=default_current_payment, key="current_payment_input")
    debt_submitted = st.form_submit_button(debt_submit_label)

if debt_submitted:
    new_debt = {
        "Debt Name": debt_name,
        "Amount Owed": amount_owed,
        "Interest Rate": interest_rate,
        "Minimum Payment": min_payment,
        "Current Payment": current_payment
    }
    if debt_mode == "edit":
        st.session_state.debts[st.session_state.editing_debt_index] = new_debt
        st.session_state.editing_debt_index = None  # exit edit mode
        st.sidebar.success(f"Debt '{debt_name}' updated!")
    else:
        st.session_state.debts.append(new_debt)
        st.sidebar.success(f"Debt '{debt_name}' added!")

# =============================================================================
# Sidebar: Investment Input / Edit Form
# =============================================================================
st.sidebar.header("Investment / Savings Details")

if st.session_state.editing_investment_index is not None:
    inv_mode = "edit"
    inv_idx = st.session_state.editing_investment_index
    inv_record = st.session_state.investments[inv_idx]
    default_invest_name = inv_record["Investment Name"]
    default_current_amount = inv_record["Current Amount"]
    default_monthly_contribution = inv_record["Monthly Contribution"]
    default_return_rate = inv_record["Return Rate"]
    inv_form_title = "Edit Investment / Savings"
    inv_submit_label = "Save Changes"
else:
    inv_mode = "add"
    default_invest_name = ""
    default_current_amount = 0.0
    default_monthly_contribution = 0.0
    default_return_rate = 0.0
    inv_form_title = "Add Investment / Savings"
    inv_submit_label = "Add Investment / Savings"

st.sidebar.subheader(inv_form_title)
with st.sidebar.form("investment_form", clear_on_submit=True):
    invest_name = st.text_input("Investment Name", value=default_invest_name, key="invest_name_input")
    current_amount = st.number_input("Current Amount", min_value=0.0, value=default_current_amount, key="current_amount_input")
    monthly_contribution = st.number_input("Monthly Contribution", min_value=0.0, value=default_monthly_contribution, key="monthly_contribution_input")
    return_rate = st.number_input("Return Rate (%)", min_value=0.0, value=default_return_rate, key="return_rate_input")
    inv_submitted = st.form_submit_button(inv_submit_label)

if inv_submitted:
    new_inv = {
        "Investment Name": invest_name,
        "Current Amount": current_amount,
        "Monthly Contribution": monthly_contribution,
        "Return Rate": return_rate
    }
    if inv_mode == "edit":
        st.session_state.investments[st.session_state.editing_investment_index] = new_inv
        st.session_state.editing_investment_index = None  # exit edit mode
        st.sidebar.success(f"Investment '{invest_name}' updated!")
    else:
        st.session_state.investments.append(new_inv)
        st.sidebar.success(f"Investment '{invest_name}' added!")

# =============================================================================
# Main Page: Display Debts in Table Format with an Edit Button per Row
# =============================================================================
st.title("Debt vs. Investment Optimization Calculator")

if not st.session_state.debts and not st.session_state.investments:
    st.info("Please add some debts and/or investments using the sidebar.")
else:
    # ----- Debts Table -----
    if st.session_state.debts:
        st.subheader("Debts Overview")
        debt_header_cols = st.columns([1, 2, 2, 2, 2, 2, 2])
        debt_header_cols[0].markdown("**Action**")
        debt_header_cols[1].markdown("**Debt Name**")
        debt_header_cols[2].markdown("**Amount Owed**")
        debt_header_cols[3].markdown("**Interest Rate**")
        debt_header_cols[4].markdown("**Min Payment**")
        debt_header_cols[5].markdown("**Current Payment**")
        debt_header_cols[6].markdown("**Estimated Payoff Date**")
        
        for i, debt in enumerate(st.session_state.debts):
            debt_row_cols = st.columns([1, 2, 2, 2, 2, 2, 2])
            if debt_row_cols[0].button("Edit", key=f"edit_debt_{i}"):
                st.session_state.editing_debt_index = i
                st.rerun()  # Prepopulate sidebar form for debt editing
            debt_row_cols[1].write(debt["Debt Name"])
            debt_row_cols[2].write(f"${debt['Amount Owed']:,}")
            debt_row_cols[3].write(f"{debt['Interest Rate']}%")
            debt_row_cols[4].write(f"${debt['Minimum Payment']:,}")
            debt_row_cols[5].write(f"${debt['Current Payment']:,}")
            months = calculate_payoff_months(debt["Amount Owed"], debt["Interest Rate"], debt["Current Payment"])
            if months is None:
                payoff_date = "Never (Payment too low)"
            else:
                payoff_date = (datetime.today() + timedelta(days=30 * months)).strftime("%Y-%m")
            debt_row_cols[6].write(payoff_date)

    # ----- Investments Table -----
    if st.session_state.investments:
        st.subheader("Investments / Savings Overview")
        inv_header_cols = st.columns([1, 3, 2, 2, 2])
        inv_header_cols[0].markdown("**Action**")
        inv_header_cols[1].markdown("**Investment Name**")
        inv_header_cols[2].markdown("**Current Amount**")
        inv_header_cols[3].markdown("**Monthly Contribution**")
        inv_header_cols[4].markdown("**Return Rate (%)**")
        
        for i, inv in enumerate(st.session_state.investments):
            inv_row_cols = st.columns([1, 3, 2, 2, 2])
            if inv_row_cols[0].button("Edit", key=f"edit_inv_{i}"):
                st.session_state.editing_investment_index = i
                st.rerun()  # Prepopulate sidebar form for investment editing
            inv_row_cols[1].write(inv["Investment Name"])
            inv_row_cols[2].write(f"${inv['Current Amount']:,}")
            inv_row_cols[3].write(f"${inv['Monthly Contribution']:,}")
            inv_row_cols[4].write(f"{inv['Return Rate']}%")

    # =============================================================================
    # Net Worth Projection and Strategy Recommendation
    # =============================================================================
    st.subheader("Net Worth Projection")
    horizon_months = st.number_input("Projection Horizon (months)", min_value=1, value=60, step=1)
    projection_df = net_worth_over_time(st.session_state.debts, st.session_state.investments, int(horizon_months))
    st.line_chart(projection_df.set_index("Month")[["Net Worth", "Total Debt", "Total Investments"]])
    final_net_worth = projection_df.iloc[-1]["Net Worth"]
    st.write(f"**Projected Net Worth after {horizon_months} months:** ${final_net_worth:,.2f}")

    st.subheader("Strategy Recommendation")
    if st.session_state.debts and st.session_state.investments:
        highest_debt_interest = max(debt["Interest Rate"] for debt in st.session_state.debts)
        avg_inv_return = np.mean([inv["Return Rate"] for inv in st.session_state.investments])
        if highest_debt_interest > avg_inv_return:
            st.info(
                f"Your highest debt interest rate ({highest_debt_interest:.2f}%) exceeds "
                f"your average investment return ({avg_inv_return:.2f}%). Consider focusing on paying off your debt faster."
            )
        else:
            st.info(
                f"Your investment returns ({avg_inv_return:.2f}%) are competitive with your debt interest rates "
                f"({highest_debt_interest:.2f}%). A balanced approach of investing while meeting debt obligations might be optimal."
            )
    elif st.session_state.debts:
        st.info("You only have debts. Prioritize debt repayment!")
    elif st.session_state.investments:
        st.info("You only have investments. Continue contributing to your investments!")




