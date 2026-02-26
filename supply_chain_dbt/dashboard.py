import streamlit as st
import pandas as pd
import snowflake.connector
import plotly.express as px

st.set_page_config(page_title="Supply Chain Risk Radar", layout="wide")

# 1. Connection Function
def get_data():
    # Streamlit automatically finds the secrets.toml file
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )
    query = "SELECT * FROM FCT_DELIVERY_PERFORMANCE"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🚚 Supply Chain Performance Dashboard")
st.markdown("Analyzing late delivery rates by country and city.")

# 2. Load Data
df = get_data()

# 3. Key Metrics (The "At a Glance" section)
col1, col2, col3 = st.columns(3)
col1.metric("Total Items Processed", f"{df['TOTAL_ORDERS'].sum():,}")
avg_late = df['LATE_DELIVERY_RATE_PCT'].mean()
col2.metric("Avg Late Rate", f"{avg_late:.2f}%", delta="-1.2%" if avg_late < 50 else "High Risk")
col3.metric("Total Countries", len(df['COUNTRY'].unique()))

# 4. Visualizations
st.subheader("Top 10 Riskest Countries")
# We'll use Plotly for a nice interactive bar chart
fig = px.bar(df.nlargest(10, 'LATE_DELIVERY_RATE_PCT'), 
             x='COUNTRY', y='LATE_DELIVERY_RATE_PCT', 
             color='LATE_DELIVERY_RATE_PCT',
             title="Countries with Highest % of Late Deliveries")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📍 Global Delivery Risk Map")

# This creates a world map where darker red = higher late delivery %
fig_map = px.choropleth(
    df,
    locations="COUNTRY",
    locationmode="country names",
    color="LATE_DELIVERY_RATE_PCT",
    hover_name="COUNTRY",
    color_continuous_scale="Reds",
    title="Late Delivery Percentage by Country"
)

st.plotly_chart(fig_map, use_container_width=True)
st.dataframe(df)

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

st.divider()
st.header("🔮 AI Delivery Predictor")
st.write("Predict if a future order will be late based on historical patterns.")

# 1. Prepare Data for ML
# We need to turn text (Countries) into numbers the computer understands
le_country = LabelEncoder()
le_city = LabelEncoder()

ml_df = df.copy().dropna()
ml_df['COUNTRY_CODE'] = le_country.fit_transform(ml_df['COUNTRY'])
ml_df['CITY_CODE'] = le_city.fit_transform(ml_df['CITY'])

# 2. Define Features and Target
X = ml_df[['COUNTRY_CODE', 'CITY_CODE', 'TOTAL_SALES']]
y = ml_df['LATE_ORDERS'].apply(lambda x: 1 if x > 0 else 0) # Binary target

# 3. Train a Simple Model
model = RandomForestClassifier(n_estimators=100, max_depth=5)
model.fit(X, y)

# 4. User Input for Prediction
st.subheader("Test a New Order Scenario")
col_a, col_b, col_c = st.columns(3)

input_country = col_a.selectbox("Select Country", df['COUNTRY'].unique())
input_city = col_b.selectbox("Select City", df[df['COUNTRY'] == input_country]['CITY'].unique())
input_sales = col_c.number_input("Order Value ($)", value=100.0)

# 5. Run Prediction
country_encoded = le_country.transform([input_country])
city_encoded = le_city.transform([input_city])

prediction = model.predict([[country_encoded[0], city_encoded[0], input_sales]])
probability = model.predict_proba([[country_encoded[0], city_encoded[0], input_sales]])

if prediction[0] == 1:
    st.error(f"⚠️ **High Risk of Delay!** (Confidence: {probability[0][1]:.2%})")
else:
    st.success(f"✅ **Likely On-Time** (Confidence: {probability[0][0]:.2%})")