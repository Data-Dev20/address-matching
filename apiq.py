# 📦 Required Libraries
import streamlit as st
import pandas as pd
import requests
import io
import time
from sklearn.cluster import KMeans
import plotly.express as px

# 🔑 Set your Geoapify API Key here
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"

# 📍 Geocode Address Function
def geocode_address(address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res["features"][0]["geometry"]["coordinates"]
        return coords[1], coords[0]  # lat, lon
    except:
        return None, None

# 📊 Streamlit App
st.title("📦 Courier Assignment, Clustering & Agent Planning")
st.markdown("Upload your Excel file and automatically assign delivery areas and agents smartly!")

# 1. Upload File
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("File uploaded successfully!")

    # ✨ Display initial rows
    st.dataframe(df.head())

    # 2. Preprocessing
    df['Address'] = df['Address'].astype(str).str.strip().str.lower()
    df['R_City'] = df['R_City'].astype(str).str.strip().str.lower()
    df['Pincode'] = df['Pincode'].astype(str).str.strip()

    st.markdown("### 🧮 Set Assignment Rules")
    min_qty = st.number_input("Minimum Roll Count (Per Entry)", value=1)
    max_qty = st.number_input("Maximum Roll Count (Per Entry)", value=500)
    rolls_per_agent = st.number_input("Max Roll Count Per Agent (Per Day)", value=200)
    cluster_count = st.number_input("Number of Clusters", value=5, min_value=1)

    # Filter by Roll Count
    filtered = df[(df['Roll Count'] >= min_qty) & (df['Roll Count'] <= max_qty)].copy()

    # 3. Geocode addresses
    st.markdown("### 🌍 Geocoding Addresses...")
    latitudes, longitudes = [], []
    with st.spinner("Fetching coordinates..."):
        for i, row in filtered.iterrows():
            full_address = f"{row['Address']}, {row['R_City']}, {row['Pincode']}"
            lat, lon = geocode_address(full_address)
            latitudes.append(lat)
            longitudes.append(lon)
            time.sleep(0.1)  # Sleep to respect API rate limit

    filtered['Latitude'] = latitudes
    filtered['Longitude'] = longitudes
    filtered = filtered.dropna(subset=['Latitude', 'Longitude'])

    # 4. Clustering
    st.markdown("### 📌 Clustering Addresses Area-wise...")
    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    filtered['Cluster'] = kmeans.fit_predict(filtered[['Latitude', 'Longitude']])

    # 5. Show Cluster Map
    st.markdown("### 🗺️ Area Clustering Map")
    fig = px.scatter_mapbox(
        filtered,
        lat="Latitude",
        lon="Longitude",
        color="Cluster",
        hover_name="Address",
        hover_data=["Roll Count", "Pincode"],
        zoom=10,
        height=500
    )
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig)

    # 6. Agent Assignment
    st.markdown("### 👥 Assign Agents Based on Roll Count Limit")
    assignments = []
    agent_id = 1
    day = 1
    current_total = 0

    for _, row in filtered.sort_values(by='Cluster').iterrows():
        qty = row['Roll Count']
        if current_total + qty > rolls_per_agent:
            day += 1
            current_total = 0
        current_total += qty
        assignments.append({
            'Cnote No': row['Cnote No'],
            'Cluster': row['Cluster'],
            'Agent': f'Agent {agent_id}',
            'Day': day
        })

    # 7. Merge Assignment with Original Data
    assignments_df = pd.DataFrame(assignments)
    final_df = pd.merge(df, assignments_df, on='Cnote No', how='left')

    # 8. Show Final Data
    st.markdown("### 📄 Final Data With Cluster, Agent & Day")
    st.dataframe(final_df)

    # 9. Download Option
    st.markdown("### 📥 Download Updated Excel File")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label="Download Full Data with Assignment",
        data=output,
        file_name="Courier_Assignments.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
