import streamlit as st
import pandas as pd
import random
import openai

openai.api_key = "YOUR_API_KEY_HERE"

st.set_page_config(page_title="AI Whitespace Sales Assistant", page_icon="📈", layout="wide")
st.title("📈 AI-Powered Whitespace Sales Assistant")

st.write("Upload a CSV with columns:")
st.code("Account, Contact, Order ID, Order Date, Category, Spend", language="text")

uploaded_file = st.file_uploader("Upload Ship-To Data (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # ---- Peer Category Frequencies ----
    category_counts = df.groupby("Category")["Account"].nunique().reset_index(name="Accounts Buying")
    total_accounts = df["Account"].nunique()
    category_counts["% Accounts Buying"] = (category_counts["Accounts Buying"] / total_accounts * 100).round(1)

    # ---- Categories per Account ----
    account_categories = df.groupby("Account")["Category"].apply(set).reset_index()

    # ---- Build Whitespace Table ----
    whitespace_rows = []
    for _, row in account_categories.iterrows():
        acct = row["Account"]
        current_cats = row["Category"]
        for _, cat_row in category_counts.iterrows():
            if cat_row["Category"] not in current_cats:
                whitespace_rows.append({
                    "Account": acct,
                    "Current Categories": ", ".join(current_cats),
                    "Missing Category": cat_row["Category"],
                    "% Peers Buying": cat_row["% Accounts Buying"]
                })

    df_whitespace = pd.DataFrame(whitespace_rows)
    df_whitespace_sorted = df_whitespace.sort_values(by=["Account", "% Peers Buying"], ascending=[True, False])
    df_top3 = df_whitespace_sorted.groupby("Account").head(3).reset_index(drop=True)

    st.subheader("🔍 Whitespace Opportunities (Top 3 per Account)")
    st.dataframe(df_top3, hide_index=True)

    # ---- Export CSV ----
    csv = df_top3.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Download Whitespace CSV", csv, "whitespace_opportunities.csv", "text/csv")

    # ---- Generate AI Recommendations ----
    if st.button("✨ Generate AI Recommendations"):
        results = []
        for _, row in df_top3.iterrows():
            prompt = f"""
            You are a sales rep at Grainger. 
            Account: {row['Account']}
            Current Categories: {row['Current Categories']}
            Whitespace Category to Pitch: {row['Missing Category']}
            % of peers buying this category: {row['% Peers Buying']}%

            TASK:
            1. Suggest ONE product in this category to pitch.
            2. Write a short call opener that references their past purchases.
            3. Suggest one discovery question.
            4. Write a short follow-up email.
            """

            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )

            results.append({
                "Account": row["Account"],
                "Category to Pitch": row["Missing Category"],
                "AI Recommendation": response["choices"][0]["message"]["content"].strip()
            })

        st.subheader("🧠 AI Recommendations + Talk Tracks")
        st.write(pd.DataFrame(results))
