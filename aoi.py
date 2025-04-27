# 📦 Required Libraries
import streamlit as st
import pandas as pd
import requests
from sklearn.cluster import KMeans
import time

# 🔑 Set your Geoapify API Key here
GEOAPIFY_API_KEY = "c2cffc22843b45ffb02d582d3d0a9eaf"

# 📍 Convert address to coordinates using Geoapify
def geocode_address(address):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={address}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url).json()
        coords = res["features"][0]["geometry"]["coordinates"]
        return coords[1], coords[0]  # lat, lon
    except:
        return None, None

# 📊 Streamlit App
st.title("📦 Courier Assignment & Clustering")
st.markdown("Upload your file and define delivery clustering & agent assignment rules.")

# 1. Upload file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("File uploaded successfully!")

    # Clean addresses
    df['Address'] = df['Address'].astype(str).str.strip().str.lower()

    # Map address to MID (first occurrence)
    address_to_mid = df.drop_duplicates('Address')[['Address', 'MID']].set_index('Address').to_dict()['MID']

    # Group by address
    grouped = df.groupby('Address').agg({
        'Roll Qty': 'sum',
        'Pincode': 'first',
        'City': 'first',
        'Zone': 'first'
    }).reset_index()

    # Add MID back
    grouped['MID'] = grouped['Address'].map(address_to_mid)

    st.markdown("### 🧮 Set Assignment Rules")

    # 2. Input filters
    min_qty = st.number_input("Minimum Roll Qty (Per Entry)", value=190)
    max_qty = st.number_input("Maximum Roll Qty (Per Entry)", value=300)
    max_per_agent = st.number_input("Max Roll Qty Per Agent (Per Day)", value=200)
    cluster_count = st.number_input("Number of Clusters", value=5, min_value=1)

    # 3. Filter valid entries
    filtered = grouped[(grouped['Roll Qty'] >= min_qty) & (grouped['Roll Qty'] <= max_qty)].copy()

    # 4. Geocode addresses (with progress)
    st.markdown("### 🌍 Geocoding Addresses...")
    latitudes, longitudes = [], []
    with st.spinner("Geocoding addresses..."):
        for i, row in filtered.iterrows():
            lat, lon = geocode_address(row['Address'] + ", " + row['City'])
            latitudes.append(lat)
            longitudes.append(lon)
            time.sleep(0.2)  # avoid rate limits

    filtered['Latitude'] = latitudes
    filtered['Longitude'] = longitudes
    filtered = filtered.dropna(subset=['Latitude', 'Longitude'])

    # 5. Clustering
    st.markdown("### 📌 Clustering Locations...")
    kmeans = KMeans(n_clusters=cluster_count, random_state=42)
    filtered['Cluster'] = kmeans.fit_predict(filtered[['Latitude', 'Longitude']])

    # 6. Agent Assignment
    st.markdown("### 👥 Assigning to Agents...")
    assignments = []
    agent_id = 1
    current_total = 0

    for _, row in filtered.sort_values(by='Cluster').iterrows():
        qty = row['Roll Qty']
        if current_total + qty > max_per_agent:
            agent_id += 1
            current_total = 0
        current_total += qty
        assignments.append({
            'Agent': f'Agent {agent_id}',
            'MID': row['MID'],
            'Address': row['Address'],
            'Roll Qty': qty,
            'Pincode': row['Pincode'],
            'Latitude': row['Latitude'],
            'Longitude': row['Longitude']
        })

    result_df = pd.DataFrame(assignments)
    st.dataframe(result_df)

    # 7. Download option
    st.markdown("### 📥 Download Assignment")
    st.download_button("Download Excel", result_df.to_excel(index=False), file_name="Agent_Assignments.xlsx")
