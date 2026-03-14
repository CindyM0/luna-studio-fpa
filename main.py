import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os

col_save1, col_save2 = st.columns([1, 5])

with col_save1:
    if st.button("Save This Month"):
        save_month_data(
            month=month,
            cash_collected=cash_collected,
            opening_deferred=opening_deferred,
            revenue_df=edited_revenue[["Service", "Sessions", "Price"]],
            expenses_df=edited_expenses,
        )
        st.success(f"{month} data saved!")
        
st.set_page_config(page_title="Luna Pawtrait Studio - P&L", layout="wide")

DATA_FILE = "pnl_data.json"

DEFAULT_EXPENSES = [
    {"Category": "Monthly", "Item": "Rent / HOA", "Amount": 1436.50},
    {"Category": "Monthly", "Item": "Business insurance", "Amount": 35.17},
    {"Category": "Monthly", "Item": "Phone", "Amount": 40.00},
    {"Category": "Monthly", "Item": "Electricity", "Amount": 0.00},
    {"Category": "Variable", "Item": "Supplies", "Amount": 380.71},
    {"Category": "One-time", "Item": "Furniture", "Amount": 1935.97},
    {"Category": "One-time", "Item": "Zoning clearance", "Amount": 175.35},
]

DEFAULT_REVENUE = [
    {"Service": "Group Class", "Sessions": 0, "Price": 0.0},
    {"Service": "Private Lesson", "Sessions": 0, "Price": 0.0},
]


def load_all_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_all_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_month_data(month):
    all_data = load_all_data()
    return all_data.get(
        month,
        {
            "cash_collected": 1670.0,
            "opening_deferred": 0.0,
            "revenue_items": DEFAULT_REVENUE,
            "expenses": DEFAULT_EXPENSES,
        },
    )


def save_month_data(month, cash_collected, opening_deferred, revenue_df, expenses_df):
    all_data = load_all_data()
    all_data[month] = {
        "cash_collected": float(cash_collected),
        "opening_deferred": float(opening_deferred),
        "revenue_items": revenue_df.to_dict(orient="records"),
        "expenses": expenses_df.to_dict(orient="records"),
    }
    save_all_data(all_data)


st.title("Luna Pawtrait Studio")
st.subheader("Monthly P&L (with Deferred Revenue)")

# -----------------------------
# 1) Month selector and Save button
# -----------------------------

months = pd.date_range(start="2026-01", end="2026-12", freq="MS")
month_options = [m.strftime("%Y-%m") for m in months]
month = st.selectbox("Select Month", month_options, index=0)


        
month_data = get_month_data(month)

# -----------------------------
# 2) Revenue inputs (editable table)
# -----------------------------
#st.markdown("### Revenue Breakdown")



# -----------------------------
# 3) Cash / Deferred inputs
# -----------------------------
st.markdown("### Cash & Deferred Revenue")
default_revenue = pd.DataFrame(month_data.get("revenue_items", DEFAULT_REVENUE))

edited_revenue = st.data_editor(
    default_revenue,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Service": st.column_config.TextColumn(
            "Service Type",
            required=True,
            help="例如 Group Class / Private Lesson / Workshop",
        ),
        "Sessions": st.column_config.NumberColumn(
            "Sessions",
            min_value=0,
            step=1,
            required=True,
            help="上了多少节",
        ),
        "Price": st.column_config.NumberColumn(
            "Price per Session",
            min_value=0.0,
            step=10.0,
            format="%.2f",
            required=True,
            help="每节单价",
        ),
    },
    key=f"revenue_editor_{month}",
)

edited_revenue["Sessions"] = pd.to_numeric(
    edited_revenue["Sessions"], errors="coerce"
).fillna(0)

edited_revenue["Price"] = pd.to_numeric(
    edited_revenue["Price"], errors="coerce"
).fillna(0.0)

edited_revenue["Revenue"] = edited_revenue["Sessions"] * edited_revenue["Price"]
recognized_revenue = float(edited_revenue["Revenue"].sum())


col1, col2 = st.columns(2)
cash_collected = float(edited_revenue["Revenue"].sum())


with col1:
    st.metric(
    "Cash Collected (收款)",
    f"{cash_collected:,.2f}"
    )

with col2:
    opening_deferred = st.number_input(
        "Opening deferred revenue (期初递延收入)",
        min_value=0.0,
        value=float(month_data["opening_deferred"]),
        step=10.0,
        help="上个月末尚未确认的预收收入",
    )

deferred_change = cash_collected - recognized_revenue
ending_deferred = opening_deferred + deferred_change

st.info(
    f"Deferred revenue change (当月递延变动) = Cash {cash_collected:.2f} - Recognized {recognized_revenue:.2f} = **{deferred_change:.2f}**\n\n"
    f"Ending deferred revenue (期末递延) = Opening {opening_deferred:.2f} + Change {deferred_change:.2f} = **{ending_deferred:.2f}**"
)

# -----------------------------
# 4) Expense inputs (editable table)
# -----------------------------
st.markdown("### Expenses")

default_expenses = pd.DataFrame(month_data["expenses"])

edited_expenses = st.data_editor(
    default_expenses,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "Category": st.column_config.SelectboxColumn(
            "Category",
            options=["Monthly", "Variable", "One-time"],
            required=True,
        ),
        "Item": st.column_config.TextColumn(
            "Item",
            required=True,
        ),
        "Amount": st.column_config.NumberColumn(
            "Amount",
            min_value=0.0,
            step=10.0,
            format="%.2f",
            required=True,
        ),
    },
    key=f"expenses_editor_{month}",
)

edited_expenses["Amount"] = pd.to_numeric(
    edited_expenses["Amount"], errors="coerce"
).fillna(0.0)



# -----------------------------
# 6) Cost calculations
# -----------------------------
fixed_cost = float(
    edited_expenses.loc[edited_expenses["Category"] == "Monthly", "Amount"].sum()
)
variable_cost = float(
    edited_expenses.loc[edited_expenses["Category"] == "Variable", "Amount"].sum()
)
one_time_cost = float(
    edited_expenses.loc[edited_expenses["Category"] == "One-time", "Amount"].sum()
)
total_expense = fixed_cost + variable_cost + one_time_cost

# -----------------------------
# 7) Revenue structure chart
# -----------------------------
st.markdown("### Revenue Structure")

revenue_chart_df = edited_revenue.copy()
revenue_chart_df = revenue_chart_df[revenue_chart_df["Revenue"] > 0]

if not revenue_chart_df.empty:
    fig_revenue = px.pie(
        revenue_chart_df,
        names="Service",
        values="Revenue",
        hole=0.35,
    )
    fig_revenue.update_traces(
        textinfo="percent+label",
        textfont_size=14,
        hovertemplate="<b>%{label}</b><br>Revenue: %{value:,.2f}<br>Share: %{percent}<extra></extra>"
    )
    fig_revenue.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    st.plotly_chart(fig_revenue, use_container_width=False)
else:
    st.info("No revenue data to display.")

# -----------------------------
# 8) Cost structure chart
# -----------------------------
st.markdown("### Cost Structure")

cost_df = pd.DataFrame({
    "Category": ["Fixed (Monthly)", "Variable", "One-time"],
    "Amount": [fixed_cost, variable_cost, one_time_cost]
})
cost_df = cost_df[cost_df["Amount"] > 0]

if not cost_df.empty:
    fig = px.pie(
        cost_df,
        names="Category",
        values="Amount",
        hole=0.35,
        color="Category",
        color_discrete_map={
            "Fixed (Monthly)": "#4C78A8",
            "Variable": "#F58518",
            "One-time": "#E45756"
        }
    )
    fig.update_traces(
        textinfo="percent+label",
        textfont_size=14,
        textfont_color="white",
        hovertemplate="<b>%{label}</b><br>Amount: %{value:,.2f}<br>Share: %{percent}<extra></extra>"
    )
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=False)
else:
    st.info("No expense data to display.")

# -----------------------------
# 9) Break-even calculator
# -----------------------------
st.markdown("### Break-even View")

positive_price_rows = edited_revenue[edited_revenue["Price"] > 0]

if not positive_price_rows.empty:
    avg_price = float(positive_price_rows["Price"].mean())
    break_even_sessions = fixed_cost / avg_price if avg_price > 0 else 0

    col_be1, col_be2, col_be3 = st.columns(3)
    col_be1.metric("Average Price / Session", f"{avg_price:,.2f}")
    col_be2.metric("Fixed Cost", f"{fixed_cost:,.2f}")
    col_be3.metric("Break-even Sessions", f"{break_even_sessions:.1f}")
else:
    st.info("Add at least one service price to estimate break-even sessions.")

# -----------------------------
# 10) P&L output
# -----------------------------
st.markdown("### Monthly P&L")

gross_profit = recognized_revenue - variable_cost
operating_income = recognized_revenue - (fixed_cost + variable_cost)
net_income = recognized_revenue - total_expense

summary = pd.DataFrame(
    [
        {"Line": "Recognized revenue (确认收入)", "Amount": recognized_revenue},
        {"Line": "Variable costs (可变成本)", "Amount": -variable_cost},
        {"Line": "Gross profit (毛利)", "Amount": gross_profit},
        {"Line": "Fixed costs (固定费用)", "Amount": -fixed_cost},
        {"Line": "Operating income (经营利润, 不含一次性)", "Amount": operating_income},
        {"Line": "One-time costs (一次性)", "Amount": -one_time_cost},
        {"Line": "Net income (净利润)", "Amount": net_income},
        {"Line": "Cash collected (收款, 非P&L)", "Amount": cash_collected},
        {"Line": "Ending deferred revenue (期末递延, 资产负债表)", "Amount": ending_deferred},
    ]
)

colA, colB, colC, colD = st.columns(4)
colA.metric("Recognized revenue", f"{recognized_revenue:,.2f}")
colB.metric("Total expense", f"{total_expense:,.2f}")
colC.metric("Net income", f"{net_income:,.2f}")
colD.metric("Ending deferred", f"{ending_deferred:,.2f}")

st.dataframe(summary, use_container_width=True)

# -----------------------------
# 11) Revenue detail summary
# -----------------------------
st.markdown("### Revenue Detail Summary")

if not revenue_chart_df.empty:
    revenue_detail = revenue_chart_df[["Service", "Sessions", "Price", "Revenue"]].copy()
    revenue_detail = revenue_detail.sort_values(by="Revenue", ascending=False)
    st.dataframe(revenue_detail, use_container_width=True)
else:
    st.write("No revenue rows yet.")

st.markdown("### Notes")
st.write(
    "- P&L 用 **确认收入**（已上课/已消耗）来算利润；\n"
    "- **收款** 不等于收入，差额会进入递延收入；\n"
    "- 一次性费用先单列，避免影响每月经营表现判断；\n"
    "- Break-even sessions 是用固定成本 ÷ 平均课单价做的简化估算。"
)
