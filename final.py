import streamlit as st
import pandas as pd
import requests
import numpy as np
import time
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
from io import BytesIO
import plotly.express as px

# Your Geoapify API Key (replace with your key)
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"

def geocode_address(address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text=38%20Upper%20Montagu%20Street%2C%20Westminster%20W1H%201LJ%2C%20United%20Kingdom&apiKey=6237e6cc370342cb96d6ae8b44539025"
        res = requests.get(url).json()
        coords = res["features"][0]["geometry"]["coordinates"]
        return coords[1], coords[0]  # lat, lon
    except:
        return None, None

def assign_agents(df, rolls_per_agent=200):
    assignments = []
    agent_id = 1
    day = 1
    current_total = 0

    for _, row in df.iterrows():
        qty = row['Roll Qty']
        if current_total + qty > rolls_per_agent:
            day += 1
            current_total = 0
        current_total += qty
        assignments.append({
            'Agent': f'Agent {agent_id}',
            'Day': day
        })

    assignment_df = pd.DataFrame(assignments)
    return pd.concat([df.reset_index(drop=True), assignment_df], axis=1)

# Streamlit App
st.title("📦 Full Courier Clustering & Agent Assignment System")
st.markdown("Upload your address file. We'll geocode, cluster, and assign agents day-by-day!")

uploaded_file = st.file_uploader("Upload Address File (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    st.markdown("### 💎 Preview Data")
    st.dataframe(df.head())

    # Basic cleaning
    df['Address'] = df['Address'].astype(str).str.strip().str.lower()
    df['Pincode'] = df['Pincode'].astype(str).str.strip()
    df['City'] = df['City'].astype(str).str.strip().str.lower()

    # Geocode addresses
    st.markdown("### 🌍 Geocoding Addresses...")
    latitudes, longitudes = [], []

    with st.spinner("Geocoding, please wait..."):
        for i, row in df.iterrows():
            full_address = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
            latitudes.append(lat)
            longitudes.append(lon)
            time.sleep(0.1)  # to respect API rate limits

    df['Latitude'] = latitudes
    df['Longitude'] = longitudes
    df = df.dropna(subset=['Latitude', 'Longitude'])

    st.success(f"Geocoding complete. {len(df)} addresses geocoded!")

    # Cluster addresses
    st.markdown("### 📌 Clustering Addresses")
    cluster_count = st.number_input("Number of Clusters", min_value=1, value=5)

    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])

    st.success("Clustering completed!")

    # Assign agents day-by-day
    st.markdown("### 👥 Assigning Deliveries to Agents Day-by-Day")
    df_sorted = df.sort_values(['Cluster', 'Latitude', 'Longitude'])
    final_df = assign_agents(df_sorted)

    st.success("Agent assignment completed!")

    # Show final data
    st.markdown("### 📝 Final Assigned Data")
    st.dataframe(final_df)

    # Map visualization (optional)
    st.markdown("### 🗻 View Clusters on Map")
    fig = px.scatter_mapbox(
        final_df,
        lat="Latitude",
        lon="Longitude",
        color="Cluster",
        hover_name="Address",
        hover_data=["Pincode", "Roll Qty", "Agent", "Day"],
        zoom=10,
        height=500
    )
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig)

    # Download final file
    st.markdown("### 📥 Download Assigned Data")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label="📦 Download Assignment File",
        data=output,
        file_name="Final_Courier_Assignment.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
