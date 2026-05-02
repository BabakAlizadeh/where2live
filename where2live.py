import pandas as pd
import streamlit as st

st.set_page_config(page_title="Texas ZIP Living Score", layout="wide")

st.title("Texas ZIP Living Score")
st.write("Find Texas ZIP codes that best match your housing and lifestyle preferences.")

# Load data
df = pd.read_csv("texas_zip_acs_scores_v0.csv")
df["zip"] = df["zip"].astype(str).str.zfill(5)

# Sidebar inputs
st.sidebar.header("Your Preferences")

metro_options = {
    "Dallas-Fort Worth": ["750", "751", "752", "760", "761", "762"],
    "Austin": ["786", "787"],
    "Houston": ["770", "773", "774", "775"],
    "San Antonio": ["780", "781", "782"],
    "All Texas": ["75", "76", "77", "78", "79"]
}

selected_metro = st.sidebar.selectbox(
    "Select your target metro area",
    list(metro_options.keys())
)

st.info(f"Currently showing results for: **{selected_metro}**")



max_rent = st.sidebar.number_input(
    "Maximum median rent you prefer ($)",
    min_value=0,
    value=2500,
    step=100
)

max_home_value = st.sidebar.number_input(
    "Maximum median home value you prefer ($)",
    min_value=0,
    value=600000,
    step=25000
)

st.sidebar.subheader("Importance Weights")

rent_weight = st.sidebar.slider("Rent affordability importance", 0, 5, 4)
home_weight = st.sidebar.slider("Home affordability importance", 0, 5, 3)
income_weight = st.sidebar.slider("Area income level importance", 0, 5, 3)

top_n = st.sidebar.slider("How many ZIP codes to show?", 5, 50, 10)

# Filter by selected metro area
filtered = df.copy()

selected_prefixes = metro_options[selected_metro]

filtered = filtered[
    filtered["zip"].astype(str).str.zfill(5).str.startswith(tuple(selected_prefixes))
]

# Filter by budget
filtered = filtered[
    (filtered["median_rent"] <= max_rent) &
    (filtered["median_home_value"] <= max_home_value)
]


# Avoid division by zero
total_weight = rent_weight + home_weight + income_weight

if total_weight == 0:
    st.warning("Please select at least one importance weight above zero.")
else:
    filtered["user_score"] = (
        rent_weight * filtered["rent_affordability_score"] +
        home_weight * filtered["home_affordability_score"] +
        income_weight * filtered["income_score"]
    ) / total_weight

    filtered = filtered.sort_values("user_score", ascending=False)

    # Create Zillow link
    filtered["zillow_link"] = filtered["zip"].apply(
        lambda z: f"https://www.zillow.com/homes/{z}_rb/"
    )

    st.subheader("Top Matching ZIP Codes")

    if filtered.empty:
        st.error("No ZIP codes match your filters. Try increasing your budget limits.")
    else:
        display_cols = [
            "zip",
            "area_name",
            "median_rent",
            "median_home_value",
            "median_income",
            "rent_affordability_score",
            "home_affordability_score",
            "income_score",
            "user_score",
            "zillow_link"
        ]

        st.dataframe(
            filtered[display_cols].head(top_n),
            use_container_width=True
        )

        st.subheader("Best Match Explanation")

        best = filtered.iloc[0]

        st.write(f"""
        Your best match is **ZIP {best['zip']}** with a score of **{best['user_score']:.2f}/10**.

        - Median rent: **${best['median_rent']:,.0f}**
        - Median home value: **${best['median_home_value']:,.0f}**
        - Median household income: **${best['median_income']:,.0f}**

        This ZIP ranked highly based on your selected affordability and income preferences.
        """)

        csv = filtered[display_cols].head(top_n).to_csv(index=False)

        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="top_zip_results.csv",
            mime="text/csv"
        )
