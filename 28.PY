import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.cluster import KMeans
import plotly.express as px
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Courier Clustering & Assignment", layout="wide")

# Your Geoapify API Key
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"

# Preprocessing function to clean and expand address shortcuts
def preprocess_address(address):
    mapping = {
        ' rd ': ' road ',
        ' marg ': ' road ',
        ' ngr ': ' nagar ',
        ' nr ': ' near ',
        ' opp ': ' opposite ',
        ' bldg ': ' building ',
        ' soc ': ' society ',
        ' apt ': ' apartment '
    }
    address = str(address).lower()
    address = ' ' + address + ' '  # Add spaces for safe replace
    for short, full in mapping.items():
        address = address.replace(short, full)
    address = address.replace(',', ' ').replace('.', ' ')
    address = ' '.join(address.split())
    return address

# Geocode function
def geocode_address(full_address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={full_address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res['features'][0]['geometry']['coordinates']
        return coords[1], coords[0]  # latitude, longitude
    except:
        return None, None

# Assign agents day-wise

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
st.title("📦 Courier Address Clustering and Agent Assignment")

uploaded_file = st.file_uploader("Upload your Excel/CSV file", type=["xlsx", "csv"])

if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext == "csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    st.subheader("🧹 Preprocessing Addresses")
    df['Address'] = df['Address'].astype(str).apply(preprocess_address)
    df['City'] = df['City'].astype(str).str.lower()
    df['Pincode'] = df['Pincode'].astype(str)

    # Geocode addresses
    st.subheader("🌍 Geocoding Addresses")
    latitudes, longitudes = [], []
    with st.spinner("Geocoding addresses..."):
        for i, row in df.iterrows():
            full_address = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
            lat, lon = geocode_address(full_address)
            latitudes.append(lat)
            longitudes.append(lon)
            time.sleep(0.2)  # Respect API limits

    df['Latitude'] = latitudes
    df['Longitude'] = longitudes
    df = df.dropna(subset=['Latitude', 'Longitude'])

    # Clustering
    st.subheader("📌 Clustering Addresses")
    cluster_count = st.number_input("Number of Clusters", min_value=1, value=5)

    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])

    color_map = px.colors.qualitative.Light24
    df['Color'] = df['Cluster'].apply(lambda x: color_map[x % len(color_map)])

    # Assign to Agents
    st.subheader("👥 Assign Deliveries to Agents")
    df_sorted = df.sort_values(['Cluster', 'Latitude', 'Longitude'])
    final_df = assign_agents(df_sorted)

    # Show updated data
    st.success("✅ Assignment Completed!")
    st.dataframe(final_df)

    # Show Cluster Map
    st.subheader("🗺️ Cluster Map Visualization")
    fig = px.scatter_mapbox(
        final_df,
        lat="Latitude",
        lon="Longitude",
        color="Cluster",
        hover_name="Address",
        hover_data=["Pincode", "Roll Qty", "Agent", "Day"],
        zoom=10,
        height=600
    )
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig)

    # Download option
    st.subheader("📥 Download Final Assigned File")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    output.seek(0)

    st.download_button(
        label="Download Assignment Excel",
        data=output,
        file_name="Assigned_Courier_Data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Footer
st.markdown("---")
st.markdown("<center>Created by Namaskar Distribution Solutions Pvt Ltd | 2025</center>", unsafe_allow_html=True)