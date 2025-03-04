import streamlit as st
import pandas as pd
import re
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle

# Load dataset
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

# Preprocess Address Column
def clean_address(address):
    """Cleans the address by removing special characters and normalizing spaces."""
    address = str(address).strip().lower()
    address = re.sub(r'[^a-zA-Z0-9\s,]', '', address)  # Keep only alphanumeric & comma
    address = re.sub(r'\s+', ' ', address)  # Normalize spaces

    # Common abbreviations replacement
    common_replacements = {
        'rd': 'road', 'st': 'street', 'ave': 'avenue', 
        'svrd': 'sv road', 'mg rd': 'mg road'
    }
    for key, val in common_replacements.items():
        address = re.sub(fr'\b{key}\b', val, address, flags=re.IGNORECASE)

    return address

# Geocode Address
def geocode_address(address, api_key):
    """Fetch latitude & longitude for an address using Geoapify API."""
    base_url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text": address, "apiKey": api_key, "format": "json"}
    response = requests.get(base_url, params=params)
    data = response.json()
    if data['results']:
        return data['results'][0]['lat'], data['results'][0]['lon']
    return None, None

# Cluster Addresses using DBSCAN
def cluster_addresses(df, eps=1.0):
    """Clusters addresses based on proximity using DBSCAN."""
    coords = df[['Latitude', 'Longitude']].values
    kms_per_radian = 6371.0088  # Earth radius in km
    db = DBSCAN(eps=eps / kms_per_radian, min_samples=2, metric='haversine').fit(np.radians(coords))
    df['Cluster'] = db.labels_
    return df

# Address Search using TF-IDF Similarity
def search_addresses(df, query, pincodes):
    """Searches addresses using TF-IDF similarity and filters by pin codes."""
    query = query.strip().lower()
    addresses = df['Address'].tolist()
    addresses.append(query)  # Append query as last item
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(addresses)
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]  # Compare query with all addresses
    sorted_indices = similarity_scores.argsort()[::-1]
    relevant_indices = [idx for idx in sorted_indices if similarity_scores[idx] > 0]
    if pincodes:
        relevant_indices = [idx for idx in relevant_indices if str(df.iloc[idx]['Pincode']) in pincodes]
    return df.iloc[relevant_indices]

# Streamlit UI
st.title("🔍 Address Filtering & Clustering System")

api_key = "YOUR_GEOAPIFY_API_KEY"  # Replace with your Geoapify API Key
uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)
    df[['Latitude', 'Longitude']] = df['Address'].apply(lambda x: pd.Series(geocode_address(x, api_key)))
    if df[['Latitude', 'Longitude']].isnull().sum().sum() == 0:
        df = cluster_addresses(df, eps=1.0)
        st.success("✅ Clustering Complete!")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Clustered Data", csv, "clustered_addresses.csv", "text/csv")
    else:
        st.warning("❌ Some addresses could not be geocoded. Check API usage.")

query = st.text_input("✍️ Enter Keywords (comma-separated):")
pincode_input = st.text_input("📍 Enter up to 2 Pincodes (comma-separated):")

if st.button("🔎 Search"):
    pincodes = [p.strip() for p in pincode_input.split(",") if p.strip().isdigit()][:2]
    result = search_addresses(df, query, pincodes)
    if len(result) > 0:
        st.success(f"✅ {len(result)} related addresses found!")
        st.dataframe(result)
        csv_result = result.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Results", csv_result, "filtered_addresses.csv", "text/csv")
    else:
        st.warning(f"❌ No results found for '{query}' with Pincode(s): {', '.join(pincodes)}.")
