import streamlit as st
import pandas as pd
import plotly.express as px

# Load data from Excel or CSV
FILE_PATH = "amazon_products.csv"   # <-- change this to .csv if your scraper saves CSV

@st.cache_data
def load_data():
    try:
        if FILE_PATH.endswith(".csv"):
            df = pd.read_csv(FILE_PATH)
        else:
            df = pd.read_excel(FILE_PATH)
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

st.set_page_config(page_title="Amazon Product Analyzer", layout="wide")
st.title("📊 Amazon Product Analyzer")
st.markdown("Explore scraped **Amazon product data** with filtering, insights, and interactive UI.")

if df.empty:
    st.error("⚠️ No data found. Please run `scraper.py` first to generate data file.")
else:
    # Sidebar Filters
    st.sidebar.header("WELCOME!")

    # Convert price to numeric
    df["price_num"] = pd.to_numeric(
        df["price"].astype(str).str.replace("$", "", regex=False).str.replace(",", "", regex=False),
        errors="coerce"
    )
    min_price, max_price = int(df["price_num"].min(skipna=True)), int(df["price_num"].max(skipna=True))
    price_range = st.sidebar.slider("Price Range ($)", min_price, max_price, (min_price, max_price))
    df = df[(df["price_num"].fillna(0) >= price_range[0]) & (df["price_num"].fillna(0) <= price_range[1])]

    # Convert rating to numeric
    df["rating_num"] = pd.to_numeric(
        df["rating"].astype(str).str.extract(r"(\d+\.\d)")[0],
        errors="coerce"
    )
    rating_filter = st.sidebar.slider("Minimum Rating", 0.0, 5.0, 0.0, step=0.1)
    df = df[df["rating_num"].fillna(0) >= rating_filter]

    # Show Data (Clickable Links)
    st.subheader("📦 Product Listings")
    for _, row in df.iterrows():
        st.markdown(f"**[{row['title']}]({row['url']})**  \n💲 {row['price']}  | ⭐ {row['rating']}")

    # Analysis
    st.subheader("📈 Analysis")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", len(df))
    with col2:
        avg_price = df["price_num"].mean(skipna=True)
        st.metric("Average Price", f"${avg_price:.2f}" if not pd.isna(avg_price) else "N/A")
    with col3:
        avg_rating = df["rating_num"].mean(skipna=True)
        st.metric("Average Rating", f"{avg_rating:.2f} ⭐" if not pd.isna(avg_rating) else "N/A")

    # Charts
    st.subheader("📊 Visual Insights")
    tab1, tab2 = st.tabs(["Price Distribution", "Rating Distribution"])
    with tab1:
        st.bar_chart(df["price_num"].dropna())
    with tab2:
        st.bar_chart(df["rating_num"].dropna())

        # Pie Chart: Product Count by Rating Category
        st.subheader("🟢 Product Count by Rating Category")
        df["rating_category"] = pd.cut(df["rating_num"], bins=[0, 2, 3.5, 5], labels=["Low", "Medium", "High"])
        rating_counts = df["rating_category"].value_counts().reset_index()
        rating_counts.columns = ["Rating Category", "Count"]
        fig = px.pie(rating_counts, names="Rating Category", values="Count", title="Product Distribution by Rating")
        st.plotly_chart(fig)
