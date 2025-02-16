import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =============================================================================
# Helper functions
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
        # if the payment is not even covering the interest, break out
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
    st.session_state.debts = []  # List of debt dicts
if "investments" not in st.session_state:
    st.session_state.investments = []  # List of investment dicts
if "editing_debt_index" not in st.session_state:
    st.session_state.editing_debt_index = None

# =============================================================================
# Sidebar: Debt Input / Edit Form
# =============================================================================
st.sidebar.title("Manage Your Finances")
st.sidebar.header("Debt Details")

# Determine if we are editing an existing debt or adding a new one
if st.session_state.editing_debt_index is not None:
    mode = "edit"
    idx = st.session_state.editing_debt_index
    debt_record = st.session_state.debts[idx]
    default_debt_name = debt_record["Debt Name"]
    default_amount_owed = debt_record["Amount Owed"]
    default_interest_rate = debt_record["Interest Rate"]
    default_min_payment = debt_record["Minimum Payment"]
    default_current_payment = debt_record["Current Payment"]
    form_title = "Edit Debt"
    submit_label = "Save Changes"
else:
    mode = "add"
    default_debt_name = ""
    default_amount_owed = 0.0
    default_interest_rate = 0.0
    default_min_payment = 0.0
    default_current_payment = 0.0
    form_title = "Add Debt"
    submit_label = "Add Debt"

st.sidebar.subheader(form_title)
with st.sidebar.form("debt_form", clear_on_submit=True):
    debt_name = st.text_input("Debt Name", value=default_debt_name, key="debt_name_input")
    amount_owed = st.number_input("Amount Owed", min_value=0.0, value=default_amount_owed, key="amount_owed_input")
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=default_interest_rate, key="interest_rate_input")
    min_payment = st.number_input("Minimum Payment", min_value=0.0, value=default_min_payment, key="min_payment_input")
    current_payment = st.number_input("Current Payment", min_value=0.0, value=default_current_payment, key="current_payment_input")
    submitted = st.form_submit_button(submit_label)

if submitted:
    new_debt = {
        "Debt Name": debt_name,
        "Amount Owed": amount_owed,
        "Interest Rate": interest_rate,
        "Minimum Payment": min_payment,
        "Current Payment": current_payment
    }
    if mode == "edit":
        st.session_state.debts[st.session_state.editing_debt_index] = new_debt
        st.session_state.editing_debt_index = None  # exit edit mode
        st.sidebar.success(f"Debt '{debt_name}' updated!")
    else:
        st.session_state.debts.append(new_debt)
        st.sidebar.success(f"Debt '{debt_name}' added!")

# =============================================================================
# Sidebar: Investment Input Form (unchanged)
# =============================================================================
st.sidebar.header("Investment / Savings Details")
with st.sidebar.form("investment_form", clear_on_submit=True):
    invest_name = st.text_input("Investment Name", key="invest_name")
    current_amount = st.number_input("Current Amount", min_value=0.0, value=0.0, key="current_amount")
    monthly_contribution = st.number_input("Monthly Contribution", min_value=0.0, value=0.0, key="monthly_contribution")
    return_rate = st.number_input("Return Rate (%)", min_value=0.0, value=0.0, key="return_rate")
    add_inv = st.form_submit_button("Add Investment")
    if add_inv:
        st.session_state.investments.append({
            "Investment Name": invest_name,
            "Current Amount": current_amount,
            "Monthly Contribution": monthly_contribution,
            "Return Rate": return_rate
        })
        st.sidebar.success(f"Investment '{invest_name}' added!")

# =============================================================================
# Main Page: Display Debts with an "Edit Debt" Button for Each
# =============================================================================
st.title("Debt vs. Investment Optimization Calculator")

if not st.session_state.debts and not st.session_state.investments:
    st.info("Please add some debts and/or investments using the sidebar.")
else:
    if st.session_state.debts:
        st.subheader("Debts Overview")
        # For each debt, display its details along with an edit button
        for i, debt in enumerate(st.session_state.debts):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{debt['Debt Name']}**")
                    st.write(f"Amount Owed: ${debt['Amount Owed']:,}")
                    st.write(f"Interest Rate: {debt['Interest Rate']}%")
                    st.write(f"Minimum Payment: ${debt['Minimum Payment']:,}")
                    st.write(f"Current Payment: ${debt['Current Payment']:,}")
                    months = calculate_payoff_months(debt["Amount Owed"], debt["Interest Rate"], debt["Current Payment"])
                    if months is None:
                        payoff_date = "Never (Payment too low)"
                    else:
                        payoff_date = (datetime.today() + timedelta(days=30 * months)).strftime("%Y-%m")
                    st.write(f"Estimated Payoff Date: {payoff_date}")
                with col2:
                    if st.button("Edit Debt", key=f"edit_debt_{i}"):
                        st.session_state.editing_debt_index = i
                        st.rerun()  # Rerun to prepopulate the sidebar form

    # =============================================================================
    # Investments Overview (Editable table remains as before)
    # =============================================================================
    if st.session_state.investments:
        st.subheader("Investments / Savings Overview")
        inv_df = pd.DataFrame(st.session_state.investments)
        edited_inv_df = st.data_editor(inv_df, num_rows="dynamic", key="investments_editor")
        st.session_state.investments = edited_inv_df.to_dict(orient="records")

    # =============================================================================
    # Net Worth and Strategy Calculation
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



