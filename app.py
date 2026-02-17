import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("🏠 Buy vs Rent — NPV Classroom Simulator")
st.caption("Developer: Dr. Shalini Velappan")

# ----------------------------------------------------
# TABS
# ----------------------------------------------------
tab1, tab2 = st.tabs(["Simulator", "Student Guide"])

# ====================================================
# ================= SIMULATOR TAB =====================
# ====================================================

with tab1:

    st.sidebar.header("Property")
    price = st.sidebar.number_input("House price", value=8000000)
    down_pct = st.sidebar.slider("Down payment %", 0.1, 0.5, 0.2)
    loan_rate = st.sidebar.number_input("Loan interest %", value=8.5)
    tenure = st.sidebar.number_input("Loan tenure years", value=20)

    st.sidebar.header("Rent")
    rent0 = st.sidebar.number_input("Monthly rent", value=25000)
    rent_growth = st.sidebar.number_input("Rent growth %", value=5)

    st.sidebar.header("Market")
    house_growth = st.sidebar.number_input("House price growth %", value=5)
    inv_return = st.sidebar.number_input("Investment return %", value=10)
    inflation = st.sidebar.number_input("Inflation %", value=5)
    disc = st.sidebar.number_input("Discount rate %", value=8)

    st.sidebar.header("Exit")
    exit_year = st.sidebar.slider("Sell after years", 3, 25, 10)

    st.sidebar.header("Costs")
    buy_commission = st.sidebar.number_input("Buy commission %", value=1.0)
    sell_commission = st.sidebar.number_input("Sell commission %", value=1.0)
    maintenance_pct = st.sidebar.number_input("Maintenance %", value=1.0)

    st.sidebar.header("Tax India")
    tax_rate = st.sidebar.number_input("Tax rate %", value=30.0)
    interest_limit = st.sidebar.number_input("Interest deduction limit", value=200000)
    principal_limit = st.sidebar.number_input("Principal deduction limit", value=150000)

    # ---------------- EMI ----------------
    loan_amt = price*(1-down_pct)
    r = loan_rate/100/12
    n = tenure*12
    emi = loan_amt*r*(1+r)**n/((1+r)**n-1)

    st.metric("Monthly EMI", f"₹{emi:,.0f}")

    # ---------------- AMORTIZATION ----------------
    balance = loan_amt
    schedule = []

    for m in range(1, exit_year*12+1):
        interest = balance*r
        principal = emi - interest
        balance -= principal
        equity = price - balance
        schedule.append([m/12, interest, principal, balance, equity])

    sched = pd.DataFrame(schedule,
        columns=["Year","Interest","Principal","Balance","Equity"])

    # ---------------- TAX FUNCTION ----------------
    def tax_saving(i, p):
        i_claim = min(i, interest_limit)
        p_claim = min(p, principal_limit)
        return (i_claim + p_claim) * tax_rate/100

    # ---------------- NPV FUNCTION ----------------
    def compute_npv(hg, rg, yrs):

        downpayment = price*down_pct
        buy_comm = price*buy_commission/100

        cf_buy = [-downpayment - buy_comm]
        cf_rent = []

        for y in range(1, yrs+1):

            rent = rent0*(1+rg/100)**y
            cf_rent.append(-(rent*12))

            yearly = sched[(sched["Year"]>y-1)&(sched["Year"]<=y)]
            interest_y = yearly["Interest"].sum()
            principal_y = yearly["Principal"].sum()

            tax = tax_saving(interest_y, principal_y)
            maintenance = price*(maintenance_pct/100)

            cf_buy.append(-(emi*12 + maintenance) + tax)

        future_price = price*(1+hg/100)**yrs
        resale = future_price*(1-sell_commission/100)
        cf_buy[-1] += resale

        invest = downpayment*(1+inv_return/100)**yrs
        cf_rent[-1] += invest

        real_disc = ((1+disc/100)/(1+inflation/100)-1)*100

        def npv(rate, cfs):
            return sum(cf/((1+rate/100)**i) for i,cf in enumerate(cfs))

        return npv(real_disc, cf_buy), npv(real_disc, cf_rent)

    # ---------------- SCENARIOS ----------------
    st.subheader("Scenario comparison")

    scenarios = {
        "Base":(house_growth, rent_growth),
        "Boom":(house_growth+3, rent_growth+2),
        "Crash":(house_growth-3, rent_growth-1)
    }

    rows=[]
    for name,(hg,rg) in scenarios.items():
        b,rn = compute_npv(hg,rg,exit_year)
        rows.append([name,b,rn,b-rn])

    df = pd.DataFrame(rows, columns=["Scenario","NPV Buy","NPV Rent","Buy-Rent"])
    st.dataframe(df)

    if (df["Buy-Rent"] < 0).any():
        st.info("In some scenarios, renting is financially better than buying.")

    # ---------------- SENSITIVITY ----------------
    st.subheader("Growth sensitivity")

    g = st.slider("House growth sensitivity", -5, 15, house_growth)
    b,rn = compute_npv(g, rent_growth, exit_year)

    col1,col2 = st.columns(2)
    col1.metric("NPV Buy", f"₹{b:,.0f}")
    col2.metric("NPV Rent", f"₹{rn:,.0f}")

    # ---------------- EQUITY CHART ----------------
    st.subheader("Equity buildup")

    fig = go.Figure()
    fig.add_scatter(x=sched["Year"], y=sched["Equity"])
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- MONTE CARLO ----------------
    st.subheader("Monte Carlo simulation")

    if st.button("Run Monte Carlo"):

        sims = 1000
        results=[]

        for _ in range(sims):
            hg = np.random.normal(house_growth,2)
            rg = np.random.normal(rent_growth,2)
            b,rn = compute_npv(hg,rg,exit_year)
            results.append(b-rn)

        prob = np.mean(np.array(results)>0)
        st.metric("Probability buying wins", f"{prob:.2%}")

        fig2 = go.Figure()
        fig2.add_histogram(x=results)
        st.plotly_chart(fig2, use_container_width=True)

# ====================================================
# ================= STUDENT GUIDE =====================
# ====================================================

with tab2:

    st.header("How to interpret results")

    st.markdown("""
### NPV decision rule
If NPV(Buy) > NPV(Rent) → Buying is better  
If NPV(Rent) > NPV(Buy) → Renting is better  

---

### When buying is better
- Long holding period  
- High property growth  
- High rent growth  
- Low interest rates  
- High tax bracket  

---

### When renting is better
Renting is financially better when:

- Short stay (0–7 years)  
- Low property price growth  
- High investment returns elsewhere  
- High interest rates  
- Mobility or job uncertainty  

Short holding periods make buying expensive due to:
- Broker commission  
- Registration cost  
- Interest-heavy EMIs  

---

### Key insight
Buying is a long-term leveraged investment.  
Renting provides flexibility and liquidity.

There is no universally correct answer.  
The decision depends on assumptions and time horizon.
""")
