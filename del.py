import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from geopy.distance import geodesic
import random

# Page Config
st.set_page_config(page_title="Delivery Assignment", page_icon="🚚", layout="wide")

st.title("🚚 Delivery Boy Assignment System")

# Upload Data
uploaded_file = st.file_uploader("📂 Upload Clustered Data (with Pincode & Cluster)", type=['csv', 'xlsx'])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Ensure Required Columns Exist
    if "Pincode" not in df.columns or "Cluster" not in df.columns or "Address" not in df.columns:
        st.error("❌ Required columns ('Pincode', 'Cluster', 'Address') are missing in the uploaded file.")
    else:
        st.success("✅ Data Loaded Successfully!")
        st.dataframe(df.head())

        # Get Unique Pincodes
        unique_pincodes = df["Pincode"].unique()

        # Assign Delivery Boys (Random for Now, Can be Optimized)
        delivery_boys = [f"Delivery_Boy_{i+1}" for i in range(5)]  # 5 Delivery Boys (Change as needed)
        df["Assigned_Delivery_Boy"] = df["Pincode"].apply(lambda x: random.choice(delivery_boys))

        # ** Clustering Nearby Locations ** (Using KMeans)
        st.subheader("📌 Optimizing Delivery Assignments...")

        # Convert Pincode to Geolocation (You can use a Geocoding API)
        pincode_centers = {
            "400001": (18.9323, 72.8346),  # Example: Mumbai CST
            "400002": (18.9553, 72.8272),  # Example: Mumbai Girgaon
            "400003": (18.9601, 72.8306),  # Example: Mumbai Mandvi
            "400004": (18.9532, 72.8238),  # Example: Mumbai Tardeo
        }

        def get_lat_lon(pincode):
            return pincode_centers.get(str(pincode), (0, 0))  # Default (0,0) for unknown

        df["Lat"], df["Lon"] = zip(*df["Pincode"].apply(get_lat_lon))

        # Remove rows with (0,0) coordinates
        df = df[df["Lat"] != 0]

        # Apply K-Means for Route Optimization
        num_clusters = len(delivery_boys)
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        df["Cluster_Group"] = kmeans.fit_predict(df[["Lat", "Lon"]])

        # Assign Delivery Boys Based on Clusters
        cluster_to_boy = {i: delivery_boys[i % len(delivery_boys)] for i in range(num_clusters)}
        df["Assigned_Delivery_Boy"] = df["Cluster_Group"].map(cluster_to_boy)

        st.success("✅ Delivery Assignment Completed!")

        # Display Results
        st.dataframe(df[["Pincode", "Cluster", "Address", "Assigned_Delivery_Boy"]])

        # Download Button
        csv_output = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Delivery Assignment", csv_output, "delivery_assignment.csv", "text/csv")
