import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from sklearn.cluster import KMeans
import plotly.express as px
from io import BytesIO

# Page Configuration
st.set_page_config(page_title="Address Assignment System", page_icon="namalogo.webp", layout="wide")

# Display logo and title in the same line
col1, col2 = st.columns([0.09, 0.9])
with col1:
    st.image("namalogo.webp", width=70)  # Use a relative path

with col2:
    st.markdown(
        "<h1 style='font-size: 32px; color: #0047AB;'>Namaskar Distribution Solutions Pvt Ltd</h1>", 
        unsafe_allow_html=True
    )

# Your Geoapify API Key
GEOAPIFY_API_KEY = "1dce308a2d0d41c4a4ed07709b5a0552"

# Preprocessing function to clean and expand address shortcuts
def preprocess_address(address):
    mapping = {
        ' rd ': ' road ', 'no': 'number', ' marg ': ' road ',
        ' ngr ': ' nagar ', ' nr ': ' near ', ' opp ': ' opposite ', 
        ' soc ': ' society ', ' apt ': ' apartment ', 'mkt' : 'market', 
        'ch' : 'church', ' bldg ': ' building ', 'mg' : 'mahatma gandhi', 
        'stn' : 'station', 'sv' : 'swami vivekananda', 'mg' : 'mahatma gandhi', 
        'govt' : 'government', 'talkies' : 'cinema', 'flr' : 'floor', 
        'sec' : 'sector', 'road' : 'marg', 'village' : 'nagar', 'lane' : 'road',
        'street' : 'road', 'avenue' : 'road', 'square' : 'road', 
    }
    address = str(address).lower()
    address = ' ' + address + ' '
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
        return coords[1], coords[0]
    except:
        return None, None

# Updated assign_agents function with separate day types and weight limits
def assign_agents(df, agent_count, rolls_per_agent=200, min_normal_weight=15, max_normal_weight=25):
    # Make a copy to avoid modifying the original
    df_sorted = df.copy()
    
    # Calculate weight if not present
    if 'Weight' not in df_sorted.columns:
        df_sorted['Weight'] = df_sorted['Roll Qty'] * 45 / 1000
    
    # Initialize assignment columns
    df_sorted['Agent'] = None
    df_sorted['Day'] = None
    df_sorted['Remark'] = None
    
    # Process cluster by cluster
    for cluster_id in sorted(df_sorted['Cluster'].unique()):
        cluster_df = df_sorted[df_sorted['Cluster'] == cluster_id].copy()
        
        # Sort by latitude and longitude within each cluster (for nearest address)
        cluster_df = cluster_df.sort_values(['Latitude', 'Longitude'])
        
        # Initialize tracking variables
        current_vehicle_day = 1
        current_normal_day = 1
        
        # Track agent data separately for vehicle and normal days
        agents_vehicle_data = {i+1: {'current_weight': 0, 'vehicle_until_day': None} for i in range(agent_count)}
        agents_normal_data = {i+1: {'current_weight': 0} for i in range(agent_count)}
        
        # Process each delivery in the cluster
        for idx, row in cluster_df.iterrows():
            weight = row['Weight']
            roll_qty = row['Roll Qty']
            
            # Determine if this delivery needs a vehicle
            needs_vehicle = weight >= 3.000
            
            if needs_vehicle:
                # Handle vehicle deliveries
                assigned_agent = None
                assigned_day = current_vehicle_day
                
                # Check if any agent already has a vehicle and can take more weight
                for agent_id in range(1, agent_count + 1):
                    if (agents_vehicle_data[agent_id]['vehicle_until_day'] is not None and 
                        agents_vehicle_data[agent_id]['vehicle_until_day'] >= current_vehicle_day and
                        agents_vehicle_data[agent_id]['current_weight'] + weight <= rolls_per_agent):
                        assigned_agent = agent_id
                        break
                
                # If no agent with vehicle available, find any agent with capacity
                if assigned_agent is None:
                    for agent_id in range(1, agent_count + 1):
                        if agents_vehicle_data[agent_id]['current_weight'] + weight <= rolls_per_agent:
                            assigned_agent = agent_id
                            break
                
                # If still no agent available, move to next vehicle day
                if assigned_agent is None:
                    current_vehicle_day += 1
                    # Reset all agents' vehicle data for the new day
                    for agent_id in range(1, agent_count + 1):
                        if agents_vehicle_data[agent_id]['vehicle_until_day'] is not None and agents_vehicle_data[agent_id]['vehicle_until_day'] < current_vehicle_day:
                            agents_vehicle_data[agent_id]['current_weight'] = 0
                            agents_vehicle_data[agent_id]['vehicle_until_day'] = None
                    
                    assigned_agent = 1  # Start with first agent on new day
                    assigned_day = current_vehicle_day
                
                # Update agent's vehicle data
                agents_vehicle_data[assigned_agent]['current_weight'] += weight
                agents_vehicle_data[assigned_agent]['vehicle_until_day'] = assigned_day + 1  # Vehicle available next day
                
                # Update assignment
                df_sorted.at[idx, 'Agent'] = f'Agent {assigned_agent}'
                df_sorted.at[idx, 'Day'] = f'V{assigned_day}'  # Mark as Vehicle day
                df_sorted.at[idx, 'Remark'] = 'Vehicle'
                
            else:
                # Handle normal deliveries
                assigned_agent = None
                assigned_day = current_normal_day
                
                # Find an agent who can take this normal delivery
                for agent_id in range(1, agent_count + 1):
                    new_weight = agents_normal_data[agent_id]['current_weight'] + weight
                    # Check if adding this weight keeps the agent within allowed range (15-30kg)
                    if min_normal_weight <= new_weight <= max_normal_weight:
                        assigned_agent = agent_id
                        break
                
                # If no agent can take it while staying within limits, find one below min_weight
                if assigned_agent is None:
                    for agent_id in range(1, agent_count + 1):
                        new_weight = agents_normal_data[agent_id]['current_weight'] + weight
                        # Only assign if it won't exceed max_weight
                        if new_weight <= max_normal_weight:
                            assigned_agent = agent_id
                            break
                
                # If still no agent available, move to next normal day
                if assigned_agent is None:
                    current_normal_day += 1
                    # Reset all agents' normal data for the new day
                    for agent_id in range(1, agent_count + 1):
                        agents_normal_data[agent_id]['current_weight'] = 0
                    
                    assigned_agent = 1  # Start with first agent on new day
                    assigned_day = current_normal_day
                
                # Update agent's normal data
                agents_normal_data[assigned_agent]['current_weight'] += weight
                
                # Update assignment
                df_sorted.at[idx, 'Agent'] = f'Agent {assigned_agent}'
                df_sorted.at[idx, 'Day'] = f'N{assigned_day}'  # Mark as Normal day
                df_sorted.at[idx, 'Remark'] = 'Normal'
    
    return df_sorted

# Streamlit App
st.title("📦 Courier Address Clustering and Agent Assignment")

uploaded_file = st.file_uploader("Upload your Excel/CSV file", type=["xlsx", "csv"])

if uploaded_file:
    agent_count = st.number_input("Enter number of available agents", min_value=1, value=5)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        rolls_per_agent = st.number_input("Max rolls per agent", min_value=1, value=200)
    with col2:
        min_normal_weight = st.number_input("Min normal weight (kg)", min_value=1, value=15)
    with col3:
        max_normal_weight = st.number_input("Max normal weight (kg)", min_value=1, value=25)

    if st.button("Start Processing"):
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

        if 'Weight' not in df.columns:
            df['Weight'] = df['Roll Qty'] * 45 / 1000
        else:
            df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce').fillna(0)

        st.subheader("🌍 Geocoding Addresses")
        latitudes, longitudes = [], []
        with st.spinner("Geocoding addresses..."):
            for i, row in df.iterrows():
                full_address = f"{row['Address']}, {row['City']}, {row['Pincode']}, India"
                lat, lon = geocode_address(full_address)
                latitudes.append(lat)
                longitudes.append(lon)
                time.sleep(0.2)

        df['Latitude'] = latitudes
        df['Longitude'] = longitudes
        df = df.dropna(subset=['Latitude', 'Longitude'])

        st.subheader("📌 Clustering Addresses")
        cluster_count = st.number_input("Number of Clusters", min_value=1, value=5)

        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(df[['Latitude', 'Longitude']])

        st.subheader("👥 Assign Deliveries to Agents")
        final_df = assign_agents(
            df, 
            agent_count, 
            rolls_per_agent=rolls_per_agent,
            min_normal_weight=min_normal_weight,
            max_normal_weight=max_normal_weight
        )

        st.success("✅ Assignment Completed!")
        st.dataframe(final_df)

        # Add statistics about assignment
        st.subheader("📊 Assignment Statistics")
        day_stats = final_df.groupby(['Agent', 'Day'])['Weight'].sum().reset_index()
        st.write("Weight by Agent and Day:")
         # Display weight distribution by Agent and Day
        fig = px.bar(day_stats, x="Agent", y="Weight", color="Day", barmode="group",
                     title="Total Assigned Weight by Agent per Day")
        st.plotly_chart(fig, use_container_width=True)

        # Download final result
        st.subheader("📥 Download Assignment File")
        buffer = BytesIO()
        final_df.to_excel(buffer, index=False)
        buffer.seek(0)
        st.download_button(
            label="Download Excel File",
            data=buffer,
            file_name="Assigned_Deliveries.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("📊 Assignment Statistics")
        st.dataframe(day_stats)
        
        # Summary for vehicle vs normal days
        day_type_stats = final_df.groupby('Remark')['Weight'].agg(['count', 'sum']).reset_index()
        day_type_stats.columns = ['Delivery Type', 'Count', 'Total Weight (kg)']
        st.write("Summary by Delivery Type:")
        st.dataframe(day_type_stats)

        st.subheader("🗺️ Cluster Map Visualization")
        fig = px.scatter_map(
            final_df,
            lat="Latitude",
            lon="Longitude",
            color="Cluster",
            hover_name="Address",
            hover_data=["Pincode", "Roll Qty", "Weight", "Agent", "Day", "Remark"],
            zoom=10,
            height=600
        )
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig)

        

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

    if st.button("🔄 Refresh App"):
        st.experimental_rerun()



# Footer Section
st.markdown("---")

st.markdown(
    """
    <div style='text-align: center; padding: 10px; font-size: 14px;'>
        <b>Namaskar Distribution Solutions Pvt Ltd</b> <br>
        Created by <b>Siddhi Patade</b> | © 2025 Address Assignment System
    </div>
    """,
    unsafe_allow_html=True
)