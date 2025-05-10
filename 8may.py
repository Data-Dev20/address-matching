import streamlit as st
import pandas as pd
import requests
import folium
from io import BytesIO
from streamlit_folium import folium_static

# === CONFIG ===
GEOAPIFY_API_KEY = "6237e6cc370342cb96d6ae8b44539025"

st.set_page_config(page_title="MID Route Planner", layout="wide")
st.title("📍 MID-Based Route Planner")
st.markdown("Upload an Excel file with `MID`, `Address`, and `Pincode` to plan delivery routes using Geoapify.")

# === Upload File ===
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    expected_cols = {"MID", "Address", "Pincode"}
    if not expected_cols.issubset(df.columns):
        st.error(f"Excel must contain these columns: {expected_cols}")
        st.stop()

    # Clean Address
    df["Address"] = df["Address"].astype(str).fillna("").str.strip()
    df["Pincode"] = df["Pincode"].astype(str).str.strip()
    df["Full_Address"] = df["Address"] + ", " + df["Pincode"]

    # === Geocode Addresses ===
    def geocode_address(address):
        url = "https://api.geoapify.com/v1/geocode/search"
        params = {
            "text": address,
            "apiKey": GEOAPIFY_API_KEY,
            "format": "json"
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            coords = data["features"][0]["geometry"]["coordinates"]
            return coords[1], coords[0]  # lat, lon
        except:
            return None, None

    with st.spinner("Geocoding addresses..."):
        df[["Latitude", "Longitude"]] = df["Full_Address"].apply(lambda x: pd.Series(geocode_address(x)))

    st.success("Geocoding completed.")
    st.dataframe(df)

    valid_df = df.dropna(subset=["Latitude", "Longitude"])
    if len(valid_df) < 2:
        st.warning("At least two valid addresses are needed to plan a route.")
        st.stop()

    # === Route Planner ===
    def get_route(df):
        latlons = [f"{row['Latitude']},{row['Longitude']}" for _, row in df.iterrows()]
        waypoints = "|".join(latlons)
        url = "https://api.geoapify.com/v1/routing"
        params = {
            "waypoints": waypoints,
            "mode": "drive",
            "apiKey": GEOAPIFY_API_KEY
        }
        response = requests.get(url, params=params)
        data = response.json()
        if "features" in data:
            props = data["features"][0]["properties"]
            coords = data["features"][0]["geometry"]["coordinates"]
            return props["distance"], props["time"], coords
        return None, None, None

    distance, time, route_coords = get_route(valid_df)

    # === Map ===
    st.subheader("🗺️ Route Map")
    route_map = folium.Map(location=[valid_df.iloc[0]["Latitude"], valid_df.iloc[0]["Longitude"]], zoom_start=12)

    for _, row in valid_df.iterrows():
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            tooltip=f"MID: {row['MID']}"
        ).add_to(route_map)

    if route_coords:
        polyline = [(lat, lon) for lon, lat in route_coords]
        folium.PolyLine(polyline, color="blue", weight=4).add_to(route_map)
        st.success(f"🚗 Distance: {distance / 1000:.2f} km | ⏱ Time: {time / 60:.2f} minutes")
    else:
        st.warning("No route found.")

    folium_static(route_map)

    # === Download Output ===
    st.subheader("📥 Download Geocoded Data")
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="📄 Download Geocoded Excel",
        data=output.getvalue(),
        file_name="geocoded_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
