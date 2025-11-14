import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

from utils.data_utils import (
    load_sales_csv,
    detect_date_column,
    detect_numeric_column,
    basic_sales_aggregates,
    aggregates_to_text,
)
from utils.ai_insights import generate_sales_insights

# Load environment variables from .env file (if it exists)
load_dotenv()

st.set_page_config(page_title="AI Sales Dashboard Agent", layout="wide")

st.title("📊 AI Sales Dashboard Agent")
st.markdown(
    "Upload a **sales CSV** and this agent will automatically generate charts and AI-powered insights."
)

# Read API key
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_KEY:
    st.warning(
        "OPENAI_API_KEY not found in environment variables. "
        "Set it before using the AI insights feature."
    )

uploaded_file = st.file_uploader("Upload Sales CSV", type=["csv"])

if uploaded_file is not None:
    # Load data
    try:
        df = load_sales_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    st.subheader("Preview of Data")
    st.dataframe(df.head())

    # Detect columns
    date_col = detect_date_column(df)
    sales_col = detect_numeric_column(df, preferred_names=["Sales", "Revenue", "Amount"])
    profit_col = detect_numeric_column(df, preferred_names=["Profit", "Margin"])

    with st.expander("Detected Columns (you can override)", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_col = st.selectbox("Date column", options=df.columns, index=df.columns.get_loc(date_col) if date_col in df.columns else 0)
        with col2:
            sales_col = st.selectbox("Sales column", options=df.columns, index=df.columns.get_loc(sales_col) if sales_col in df.columns else 0)
        with col3:
            profit_idx = df.columns.get_loc(profit_col) if profit_col in df.columns else 0
            profit_col = st.selectbox("Profit column (optional)", options=["<None>"] + list(df.columns), index=0 if profit_col is None else profit_idx + 1)
            if profit_col == "<None>":
                profit_col = None

    # Convert date column
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception as e:
        st.error(f"Could not parse date column '{date_col}': {e}")
        st.stop()

    # Sidebar filters
    st.sidebar.header("Filters")
    # Date range filter
    min_date = df[date_col].min()
    max_date = df[date_col].max()
    start_date, end_date = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(start_date, tuple):
        # Streamlit bug in some versions
        start_date, end_date = start_date

    mask = (df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))
    df_filtered = df.loc[mask].copy()

    st.sidebar.write(f"Rows after filter: {len(df_filtered)}")

    # Compute aggregates
    agg = basic_sales_aggregates(df_filtered, date_col=date_col, sales_col=sales_col, profit_col=profit_col)

    # Top KPI row
    st.subheader("Key Metrics")
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Total Sales", f"{agg['total_sales']:,.2f}")
    with kpi_cols[1]:
        if agg["total_profit"] is not None:
            st.metric("Total Profit", f"{agg['total_profit']:,.2f}")
        else:
            st.metric("Total Profit", "N/A")
    with kpi_cols[2]:
        if agg["profit_margin"] is not None:
            st.metric("Profit Margin", f"{agg['profit_margin']*100:,.2f}%")
        else:
            st.metric("Profit Margin", "N/A")
    with kpi_cols[3]:
        st.metric("Order Count", f"{agg['order_count']:,}")

    # Charts row
    st.subheader("Visualizations")
    chart_row1 = st.columns(2)

    # Sales over time
    monthly = agg["monthly_sales"]
    if monthly is not None and not monthly.empty:
        with chart_row1[0]:
            # Ensure we have column names
            if "Sales" not in monthly.columns:
                # assume second column is sales
                sales_col_month = monthly.columns[1]
                monthly = monthly.rename(columns={sales_col_month: "Sales"})
            fig_time = px.line(
                monthly,
                x="_parsed_date",
                y="Sales",
                title="Sales Over Time (Monthly)",
            )
            fig_time.update_layout(xaxis_title="Month", yaxis_title="Sales")
            st.plotly_chart(fig_time, use_container_width=True)

    # Sales by category
    category_sales = agg.get("category_sales")
    if category_sales is not None:
        with chart_row1[1]:
            if "Sales" not in category_sales.columns:
                sales_col_cat = category_sales.columns[1]
                category_sales = category_sales.rename(columns={sales_col_cat: "Sales"})
            fig_cat = px.bar(
                category_sales,
                x=agg["category_col"],
                y="Sales",
                title=f"Sales by {agg['category_col']}",
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    # Second row: region chart if available
    region_sales = agg.get("region_sales")
    if region_sales is not None:
        st.markdown("### Sales by Region")
        if "Sales" not in region_sales.columns:
            sales_col_reg = region_sales.columns[1]
            region_sales = region_sales.rename(columns={sales_col_reg: "Sales"})
        fig_reg = px.bar(
            region_sales,
            x=agg["region_col"],
            y="Sales",
            title=f"Sales by {agg['region_col']}",
        )
        st.plotly_chart(fig_reg, use_container_width=True)

    # AI Insights
    st.subheader("🤖 AI Insights")

    if not OPENAI_KEY:
        st.info("Set OPENAI_API_KEY to enable AI-generated insights.")
    else:
        if st.button("Generate AI Insights from Current View"):
            with st.spinner("Analyzing data and generating insights..."):
                summary_text = aggregates_to_text(agg)
                insights = generate_sales_insights(summary_text, api_key=OPENAI_KEY)
            st.markdown(insights)
else:
    st.info("Upload a CSV to get started.")
