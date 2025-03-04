import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =============================================================================
# Helper Functions for Debt & Investment Calculations
# =============================================================================
def calculate_payoff_months(amount, annual_interest_rate, payment):
    """
    Simulate month-by-month payoff of a debt given a fixed payment.
    Returns the number of months required to pay off the debt.
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

# -----------------------------------------------------------------------------
# New Helper: Simulate Debt Payoffs Using the Current Debt Allocation
# -----------------------------------------------------------------------------
def simulate_debt_payoffs(debts, debt_allocation, max_months=120):
    """
    Simulate month-by-month payoff for each debt using the current debt_allocation.
    
    Returns a list of payoff months for each debt. If a debt is not paid off within
    max_months, the corresponding value will be "N/A".
    """
    # Copy initial values
    debt_balances = [d["Amount Owed"] for d in debts]
    debt_min_payments = [d["Minimum Payment"] for d in debts]
    debt_interest_rates = [d["Interest Rate"]/100/12 for d in debts]
    payoff_months = [None] * len(debts)
    
    for m in range(1, max_months+1):
        active_indices = [i for i, bal in enumerate(debt_balances) if bal > 0]
        if not active_indices:
            break
        total_min = sum(debt_min_payments[i] for i in active_indices)
        payments = [0.0] * len(debt_balances)
        if active_indices:
            if debt_allocation < total_min:
                for i in active_indices:
                    payments[i] = debt_min_payments[i] * (debt_allocation / total_min)
            else:
                # First pay the minimums...
                for i in active_indices:
                    payments[i] = debt_min_payments[i]
                extra = debt_allocation - total_min
                # Allocate extra to debts in order of descending interest rate.
                sorted_active = sorted(active_indices, key=lambda i: debts[i]["Interest Rate"], reverse=True)
                for i in sorted_active:
                    if extra <= 0:
                        break
                    payment_needed = debt_balances[i] * (1 + debt_interest_rates[i])
                    extra_needed = max(payment_needed - payments[i], 0)
                    extra_payment = min(extra, extra_needed)
                    payments[i] += extra_payment
                    extra -= extra_payment
        
        # Update each debt balance
        for i in range(len(debt_balances)):
            if debt_balances[i] > 0:
                new_balance = debt_balances[i] * (1 + debt_interest_rates[i]) - payments[i]
                debt_balances[i] = max(new_balance, 0)
                if debt_balances[i] == 0 and payoff_months[i] is None:
                    payoff_months[i] = m
    # Mark any remaining debts as not paid off within the timeframe.
    for i in range(len(debt_balances)):
        if payoff_months[i] is None:
            payoff_months[i] = "N/A"
    return payoff_months

# -----------------------------------------------------------------------------
# Simulation Function: Overall Financial Simulation (Month-by-Month)
# -----------------------------------------------------------------------------
def simulate_finances(debts, explicit_investments, monthly_budget, debt_allocation, horizon_months, default_return_rate=7.0):
    """
    Simulate your finances over time with:
      - monthly_budget: total funds available each month.
      - debt_allocation: the portion of monthly_budget allocated for debt payments.
      - investment_allocation = monthly_budget - debt_allocation goes to the default investment.
    
    Returns a DataFrame with the net worth, total debt, total investments,
    default investment value, explicit investments value, and total debt payments.
    """
    # Initialize debt parameters
    debt_balances = [d["Amount Owed"] for d in debts]
    debt_min_payments = [d["Minimum Payment"] for d in debts]
    debt_interest_rates = [d["Interest Rate"]/100/12 for d in debts]
    default_balance = 0.0  # Default investment now starts at 0
    
    simulation = []
    for m in range(horizon_months + 1):
        # --- Debt Payment Allocation (using same logic as in simulate_debt_payoffs) ---
        active_indices = [i for i, bal in enumerate(debt_balances) if bal > 0]
        total_min = sum(debt_min_payments[i] for i in active_indices)
        payments = [0.0] * len(debt_balances)
        if active_indices:
            if debt_allocation < total_min:
                for i in active_indices:
                    payments[i] = debt_min_payments[i] * (debt_allocation / total_min)
            else:
                for i in active_indices:
                    payments[i] = debt_min_payments[i]
                extra = debt_allocation - total_min
                sorted_active = sorted(active_indices, key=lambda i: debts[i]["Interest Rate"], reverse=True)
                for i in sorted_active:
                    if extra <= 0:
                        break
                    payment_needed = debt_balances[i] * (1 + debt_interest_rates[i])
                    extra_needed = max(payment_needed - payments[i], 0)
                    extra_payment = min(extra, extra_needed)
                    payments[i] += extra_payment
                    extra -= extra_payment
        
        # --- Update Debt Balances ---
        for i in range(len(debt_balances)):
            if debt_balances[i] > 0:
                new_balance = debt_balances[i] * (1 + debt_interest_rates[i]) - payments[i]
                debt_balances[i] = max(new_balance, 0)
        total_debt = sum(debt_balances)
        
        # --- Default Investment Update ---
        investment_allocation = monthly_budget - debt_allocation
        if m > 0:
            default_balance = default_balance * (1 + default_return_rate/100/12) + investment_allocation
        
        # --- Explicit Investments (closed-form calculation) ---
        explicit_total = 0.0
        for inv in explicit_investments:
            explicit_total += future_value(inv["Current Amount"], inv["Monthly Contribution"], inv["Return Rate"], m)
        
        total_investments = default_balance + explicit_total
        net_worth = total_investments - total_debt
        
        simulation.append({
            "Month": m,
            "Net Worth": net_worth,
            "Total Debt": -total_debt,  # displayed as negative
            "Total Investments": total_investments,
            "Default Investment": default_balance,
            "Explicit Investments": explicit_total,
            "Debt Payments": sum(payments)
        })
    return pd.DataFrame(simulation)

# =============================================================================
# Session State Initialization
# =============================================================================
if "debts" not in st.session_state:
    st.session_state.debts = []          # List of debt dictionaries
if "investments" not in st.session_state:
    st.session_state.investments = []    # List of explicit investment dictionaries
if "editing_debt_index" not in st.session_state:
    st.session_state.editing_debt_index = None
if "editing_investment_index" not in st.session_state:
    st.session_state.editing_investment_index = None

# =============================================================================
# Sidebar Inputs: Monthly Budget, Debt/Investment Allocation, and Financial Details
# =============================================================================
st.sidebar.title("Manage Your Finances")

# ---- Monthly Available Funds ----
monthly_budget = st.sidebar.number_input("Monthly Available Funds", min_value=0.0, value=2000.0, step=100.0)

# ---- Slider: Allocate Funds to Debt vs. Investments ----
# The slider determines how much of the monthly_budget is allocated to debt payments.
debt_allocation = st.sidebar.slider(
    "Monthly Allocation to Debt Payment",
    min_value=0.0,
    max_value=monthly_budget,
    value=monthly_budget/2,
    step=100.0
)
st.sidebar.write(f"Debt Payment: ${debt_allocation:,.2f}  |  Investment Contribution: ${monthly_budget - debt_allocation:,.2f}")

# ---- Display Default Investment Parameters ----
with st.sidebar.expander("Default Investment Parameters"):
    st.write(f"**Monthly Contribution:** ${monthly_budget - debt_allocation:,.2f}")
    st.write("**Return Rate:** 7% per year")

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
    debt_form_title = "Edit Debt"
    debt_submit_label = "Save Changes"
else:
    debt_mode = "add"
    default_debt_name = ""
    default_amount_owed = 0.0
    default_interest_rate = 0.0
    default_min_payment = 0.0
    debt_form_title = "Add Debt"
    debt_submit_label = "Add Debt"

st.sidebar.subheader(debt_form_title)
with st.sidebar.form("debt_form", clear_on_submit=True):
    debt_name = st.text_input("Debt Name", value=default_debt_name, key="debt_name_input")
    amount_owed = st.number_input("Amount Owed", min_value=0.0, value=default_amount_owed, key="amount_owed_input")
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, value=default_interest_rate, key="interest_rate_input")
    min_payment = st.number_input("Minimum Payment", min_value=0.0, value=default_min_payment, key="min_payment_input")
    debt_submitted = st.form_submit_button(debt_submit_label)

if debt_submitted:
    new_debt = {
        "Debt Name": debt_name,
        "Amount Owed": amount_owed,
        "Interest Rate": interest_rate,
        "Minimum Payment": min_payment
    }
    if debt_mode == "edit":
        st.session_state.debts[st.session_state.editing_debt_index] = new_debt
        st.session_state.editing_debt_index = None
        st.sidebar.success(f"Debt '{debt_name}' updated!")
    else:
        st.session_state.debts.append(new_debt)
        st.sidebar.success(f"Debt '{debt_name}' added!")

# ---- Explicit Investment Input / Edit Form ----
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
        # Calculate updated payoff estimates using the current slider (debt_allocation)
        payoff_estimates = simulate_debt_payoffs(st.session_state.debts, debt_allocation, max_months=120)
        
        debt_header_cols = st.columns([1, 2, 2, 2, 2, 2])
        debt_header_cols[0].markdown("**Action**")
        debt_header_cols[1].markdown("**Debt Name**")
        debt_header_cols[2].markdown("**Amount Owed**")
        debt_header_cols[3].markdown("**Interest Rate**")
        debt_header_cols[4].markdown("**Min Payment**")
        debt_header_cols[5].markdown("**Optimal Payoff (Est.)**")
        
        for i, debt in enumerate(st.session_state.debts):
            debt_row_cols = st.columns([1, 2, 2, 2, 2, 2])
            if debt_row_cols[0].button("Edit", key=f"edit_debt_{i}"):
                st.session_state.editing_debt_index = i
                st.rerun()
            debt_row_cols[1].write(debt["Debt Name"])
            debt_row_cols[2].write(f"${debt['Amount Owed']:,}")
            debt_row_cols[3].write(f"{debt['Interest Rate']}%")
            debt_row_cols[4].write(f"${debt['Minimum Payment']:,}")
            # Format payoff estimate
            payoff_est = payoff_estimates[i]
            if isinstance(payoff_est, int):
                payoff_date = (datetime.today() + timedelta(days=30*payoff_est)).strftime("%Y-%m")
            else:
                payoff_date = payoff_est
            debt_row_cols[5].write(payoff_date)
    
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
    # Financial Simulation: Net Worth Projection & Cash Flow
    # =============================================================================
    st.subheader("Net Worth Projection & Cash Flow Simulation")
    horizon_months = st.number_input("Projection Horizon (months)", min_value=1, value=60, step=1)
    
    explicit_investments = st.session_state.investments.copy()
    
    sim_df = simulate_finances(
        debts=st.session_state.debts,
        explicit_investments=explicit_investments,
        monthly_budget=monthly_budget,
        debt_allocation=debt_allocation,
        horizon_months=int(horizon_months),
        default_return_rate=7.0
    )
    
    st.line_chart(sim_df.set_index("Month")[["Net Worth", "Total Debt", "Total Investments"]])
    final_net_worth = sim_df.iloc[-1]["Net Worth"]
    st.write(f"**Projected Net Worth after {horizon_months} months:** ${final_net_worth:,.2f}")
    
    # -----------------------------------------------------------------------------
    # Display the initial simulation row (Month 0) for a breakdown of the default investment.
    # -----------------------------------------------------------------------------
    with st.expander("View Initial Financial Breakdown (Month 0)"):
        st.markdown(
            "This row shows your starting point. Note that the **Default Investment** starts at $0 "
            "and each month receives the funds allocated to investments (i.e. Monthly Available Funds minus Debt Payment Allocation)."
        )
        initial_row = sim_df[sim_df["Month"] == 0]
        st.table(initial_row)
    
    # =============================================================================
    # Optimal Payoff Strategy Recommendation
    # =============================================================================
    st.subheader("Optimal Payoff Strategy")
    if st.session_state.debts:
        # Identify the highest interest rate among active debts.
        highest_debt = max(st.session_state.debts, key=lambda x: x["Interest Rate"])
        highest_debt_interest = highest_debt["Interest Rate"]
        # Compare the highest debt interest rate with the default investment return (7%)
        if highest_debt_interest > 7:
            st.info(
                f"Your highest debt interest rate is {highest_debt_interest:.2f}%, which exceeds the default investment return (7%).\n\n"
                "It may be optimal to allocate more funds toward paying off your debts."
            )
        else:
            st.info(
                f"Your highest debt interest rate is {highest_debt_interest:.2f}% (at or below the default investment return of 7%).\n\n"
                "You might consider investing more of your available funds."
            )
    else:
        st.info("No debts have been added, so all available funds are directed toward investments.")










