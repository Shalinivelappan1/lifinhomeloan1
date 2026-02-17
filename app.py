import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🏠 Buy vs Rent — NPV Classroom Simulator")
st.caption("Developer: Dr. Shalini Velappan")

tab1, tab2 = st.tabs(["Simulator", "Student Guide"])

# =====================================================
# SIMULATOR
# =====================================================
with tab1:

    # ---------------- SIDEBAR ----------------
    st.sidebar.header("Property")

    price = st.sidebar.number_input("House price", value=1500000.0)
    down_pct = st.sidebar.number_input("Down payment %", value=20.0)
    loan_rate = st.sidebar.number_input("Loan interest %", value=3.0)
    tenure = st.sidebar.number_input("Loan tenure (years)", value=30)

    st.sidebar.header("Rent")
    rent0 = st.sidebar.number_input("Monthly rent", value=4000.0)
    rent_growth = st.sidebar.number_input("Rent growth %", value=0.0)

    st.sidebar.header("Market")
    house_growth = st.sidebar.number_input("House price growth %", value=0.0)
    inv_return = st.sidebar.number_input("Investment return %", value=3.0)
    disc = st.sidebar.number_input("Discount rate %", value=3.0)

    st.sidebar.header("Exit")
    exit_year = st.sidebar.number_input("Sell after years", value=10)

    st.sidebar.header("Costs")
    buy_commission = st.sidebar.number_input("Buy commission %", value=1.0)
    sell_commission = st.sidebar.number_input("Sell commission %", value=1.0)
    monthly_costs = st.sidebar.number_input("Maintenance+tax+repairs (monthly)", value=450.0)

    # ---------------- EMI ----------------
    downpayment = price * down_pct/100
    loan_amt = price - downpayment

    r = loan_rate/100/12
    n = tenure*12

    emi = loan_amt*r*(1+r)**n/((1+r)**n-1)
    st.metric("Monthly EMI", f"{emi:,.2f}")

    # ---------------- AMORTIZATION ----------------
    balance = loan_amt
    balances = []

    for m in range(exit_year*12):
        interest = balance*r
        principal = emi - interest
        balance -= principal
        balances.append(balance)

    remaining_balance = balance

    # =====================================================
    # NPV FUNCTION (MONTHLY — CASE CONSISTENT)
    # =====================================================

    def compute_npv(hg, rg):

        months = exit_year*12
        monthly_disc = disc/100/12

        # BUY CASHFLOWS
        cf_buy = []

        # time 0
        initial = downpayment + price*buy_commission/100 + 0.03*price + 8000
        cf_buy.append(-initial)

        balance = loan_amt

        for m in range(1, months+1):

            interest = balance*r
            principal = emi - interest
            balance -= principal

            cf = -(emi + monthly_costs)
            cf_buy.append(cf)

        # resale
        sale_price = price*(1+hg/100)**exit_year
        sale_net = sale_price*(1-sell_commission/100) - balance
        cf_buy[-1] += sale_net

        # RENT CASHFLOWS
        cf_rent = [0]

        rent = rent0
        for m in range(1, months+1):
            rent = rent*(1+rg/100/12)
            cf_rent.append(-rent)

        # invest down payment
        invest = downpayment*(1+inv_return/100)**exit_year
        cf_rent[-1] += invest

        def npv(rate, cfs):
            return sum(cf/((1+rate)**i) for i, cf in enumerate(cfs))

        return npv(monthly_disc, cf_buy), npv(monthly_disc, cf_rent)

    # ---------------- SCENARIO TABLE ----------------
    st.subheader("Scenario comparison")

    scenarios = {
        "Base": (house_growth, rent_growth),
        "Boom": (house_growth+1, rent_growth),
        "Crash": (house_growth-1, rent_growth)
    }

    rows=[]
    for name,(hg,rg) in scenarios.items():
        b,rn = compute_npv(hg,rg)
        rows.append([name,b,rn,b-rn])

    df = pd.DataFrame(rows, columns=["Scenario","NPV Buy","NPV Rent","Buy-Rent"])
    st.dataframe(df)

    # ---------------- SENSITIVITY ----------------
    st.subheader("Growth sensitivity")

    g = st.slider("House growth", -5.0, 5.0, float(house_growth))
    b,rn = compute_npv(g, rent_growth)

    col1,col2 = st.columns(2)
    col1.metric("NPV Buy", f"{b:,.0f}")
    col2.metric("NPV Rent", f"{rn:,.0f}")

    # ---------------- MONTE CARLO ----------------
    st.subheader("Monte Carlo")

    if st.button("Run Monte Carlo"):
        sims=500
        results=[]
        for _ in range(sims):
            hg=np.random.normal(house_growth,1)
            rg=np.random.normal(rent_growth,1)
            b,rn = compute_npv(hg,rg)
            results.append(b-rn)

        prob = np.mean(np.array(results)>0)
        st.metric("Probability buy wins", f"{prob:.2%}")

        fig=go.Figure()
        fig.add_histogram(x=results)
        st.plotly_chart(fig,use_container_width=True)

# =====================================================
# STUDENT GUIDE
# =====================================================
with tab2:

    st.header("How to interpret results")

    st.markdown("""
### Decision rule
If NPV(Buy) > NPV(Rent) → Buy  
If NPV(Rent) > NPV(Buy) → Rent  

### When renting is better
- Short holding period  
- Low house price growth  
- High interest rates  
- High alternative investment returns  

### When buying is better
- Long stay  
- Strong price growth  
- Rising rents  

### Key insight
Small changes in assumptions flip the decision.
""")
