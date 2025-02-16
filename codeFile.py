import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =============================================================================
# Helper Functions for Debt & Investment Calculations
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
    if payment <= balance * monthly_rate:
        return None
    while balance > 0 and months < 1000:
        balance = balance * (1 + monthly_rate) - payment
        months += 1
    return months

def remaining_balance(amount, annual_interest_rate, payment, months):
    """
    Calculate remaining balance on a debt after a given number of months.
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
    Calculate the future value of an investment with fixed monthly contributions.
    """
    r = annual_return_rate / 100 / 12
    if r != 0:
        fv = current_amount * (1 + r) ** months + monthly_contribution * (((1 + r) ** months - 1) / r)
    else:
        fv = current_amount + monthly_contribution * months
    return fv

# =============================================================================
# Simulation Function: Iterative Month-by-Month Calculation
# =============================================================================
def simulate_finances(debts, explicit_investments, default_investment_initial, monthly_budget, horizon_months, default_return_rate=7.0):
    """
    Simulate your finances over time using your debts, your explicit investments,
    and a default investment category that receives any leftover cash each month.
    
    For each month:
      - Each active debt is updated with interest and a fixed payment.
      - The sum of required payments for active debts is subtracted from your monthly budget.
      - Any remaining funds are contributed to the default investment.
      - Explicit investments are calculated using a closed-form formula.
    
    Returns a DataFrame with the net worth, total (negative) debt, total investments,
    and a breakdown of default and explicit investments.
    """
    # Initialize debt balances (one per debt)
    debt_balances = [d["Amount Owed"] for d in debts]
    debt_interest_rates = [d["Interest Rate"]/100/12 for d in debts]  # monthly interest rates
    debt_payments = [d["Current Payment"] for d in debts]
    
    # Initialize the default investment balance
    default_balance = default_investment_initial

    simulation = []
    for m in range(horizon_months + 1):
        # Total outstanding debt (as a positive number)
        total_debt = sum(debt_balances)
        # Sum of required payments for debts that are still active
        active_debt_payment = sum(payment if balance > 0 else 0 
                                  for balance, payment in zip(debt_balances, debt_payments))
        
        # For month 0, no monthly contribution is added yet.
        if m > 0:
            # Funds left from the monthly budget after paying active debts:
            default_contribution = max(monthly_budget - active_debt_payment, 0)
            # Update default investment balance using compound interest on a monthly basis.
            default_balance = default_balance * (1 + default_return_rate/100/12) + default_contribution
        
        # Compute the total value of all explicit investments using the fixed formula.
        explicit_total = 0
        for inv in explicit_investments:
            explicit_total += future_value(inv["Current Amount"], inv["Monthly Contribution"], inv["Return Rate"], m)
        
        total_investments = default_balance + explicit_total
        net_worth = total_investments - total_debt  # Debt is a liability
        
        simulation.append({
            "Month": m,
            "Net Worth": net_worth,
            "Total Debt": -total_debt,  # shown as negative
            "Total Investments": total_investments,
            "Default Investment": default_balance,
            "Explicit Investments": explicit_total,
            "Debt Payments": active_debt_payment
        })
        
        # Update each debt balance for the next month.
        for i in range(len(debt_balances)):
            if debt_balances[i] > 0:
                new_balance = debt_balances[i] * (1 + debt_interest_rates[i]) - debt_payments[i]
                debt_balances[i] = max(new_balance, 0)
    return pd.DataFrame(simulation)

# =============================================================================
# Session State Initialization
# =============================================================================
if "debts" not in st.session_state:
    st.session_state.debts = []  # List of debt dictionaries
if "investments" not in st.session_state:
    st.session_state.investments = []  # List of explicit investment dictionaries
if "editing_debt_index" not in st.session_state:
    st.session_state.editing_debt_index = None
if "editing_investment_index" not in st.session_state:
    st.session_state.editing_investment_index = None

# =============================================================================
# Sidebar Inputs for Debts, Investments, and Cash Flow Parameters
# =============================================================================
st.sidebar.title("Manage Your Finances")

# ---- Cash Flow Parameters ----
st.sidebar.subheader("Budget & Savings")
monthly_budget = st.sidebar.number_input("Monthly Budget for Debt & Investing", min_value=0.0, value=2000.0, step=100.0)
default_investment_initial = st.sidebar.number_input("Initial Savings for Default Investment", min_value=0.0, value=5000.0, step=100.0)

# ---- Debt Input / Edit Form ----
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
        st.session_state.editing_debt_index = None
        st.sidebar.success(f"Debt '{debt_name}' updated!")
    else:
        st.session_state.debts.append(new_debt)
        st.sidebar.success(f"Debt '{debt_name}' added!")

# ---- Investment Input / Edit Form for Explicit Investments ----
st.sidebar.header("Explicit Investment / Savings Details")
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
    inv_form_title = "Add Explicit Investment / Savings"
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
        st.session_state.editing_investment_index = None
        st.sidebar.success(f"Investment '{invest_name}' updated!")
    else:
        st.session_state.investments.append(new_inv)
        st.sidebar.success(f"Investment '{invest_name}' added!")

# =============================================================================
# Main Page: Display Debts and Explicit Investments with Edit Buttons
# =============================================================================
st.title("Debt vs. Investment Optimization Calculator")

if not st.session_state.debts and not st.session_state.investments:
    st.info("Please add some debts and/or explicit investments using the sidebar.")
else:
    # --- Debts Table ---
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
                st.rerun()
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
    
    # --- Explicit Investments Table ---
    if st.session_state.investments:
        st.subheader("Explicit Investments / Savings Overview")
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
                st.rerun()
            inv_row_cols[1].write(inv["Investment Name"])
            inv_row_cols[2].write(f"${inv['Current Amount']:,}")
            inv_row_cols[3].write(f"${inv['Monthly Contribution']:,}")
            inv_row_cols[4].write(f"{inv['Return Rate']}%")
    
    # =============================================================================
    # Net Worth Projection & Financial Simulation
    # =============================================================================
    st.subheader("Net Worth Projection & Cash Flow Simulation")
    horizon_months = st.number_input("Projection Horizon (months)", min_value=1, value=60, step=1)
    
    # Separate explicit investments from the default (if any explicit investment is named "Default Investment", ignore it)
    explicit_investments = [inv for inv in st.session_state.investments if inv["Investment Name"] != "Default Investment"]
    
    sim_df = simulate_finances(
        debts=st.session_state.debts,
        explicit_investments=explicit_investments,
        default_investment_initial=default_investment_initial,
        monthly_budget=monthly_budget,
        horizon_months=int(horizon_months),
        default_return_rate=7.0
    )
    
    st.line_chart(sim_df.set_index("Month")[["Net Worth", "Total Debt", "Total Investments"]])
    final_net_worth = sim_df.iloc[-1]["Net Worth"]
    st.write(f"**Projected Net Worth after {horizon_months} months:** ${final_net_worth:,.2f}")
    
    # =============================================================================
    # Optimal Payoff Strategy Recommendation
    # =============================================================================
    st.subheader("Optimal Payoff Strategy")
    if st.session_state.debts and explicit_investments:
        # Identify the debt with the highest interest rate
        highest_debt = max(st.session_state.debts, key=lambda x: x["Interest Rate"])
        highest_debt_interest = highest_debt["Interest Rate"]
        avg_inv_return = np.mean([inv["Return Rate"] for inv in explicit_investments])
        
        if avg_inv_return > highest_debt_interest:
            st.info(
                f"Your average return on your explicit investments is {avg_inv_return:.2f}% which is higher than your highest debt interest rate ({highest_debt_interest:.2f}%).\n\n"
                "It may be optimal to pay only the minimum on your debts and invest extra funds."
            )
        else:
            st.info(
                f"Your highest debt interest rate is {highest_debt_interest:.2f}% which is higher than your average explicit investment return ({avg_inv_return:.2f}%).\n\n"
                f"Consider focusing extra payments on your '{highest_debt['Debt Name']}' debt to pay it off quickly; then that freed-up cash can flow into your default investment."
            )
    elif st.session_state.debts:
        st.info("You only have debts. Prioritize paying them off!")
    elif explicit_investments:
        st.info("You only have explicit investments. Continue contributing!")







