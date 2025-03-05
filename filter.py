import streamlit as st
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
import numpy as np

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

# Address Search using TF-IDF Similarity
def search_addresses(df, query1, query2, pincodes):
    """Searches addresses using TF-IDF similarity and filters by pin codes."""
    query1, query2 = query1.strip().lower(), query2.strip().lower()
    
    # Prepare address corpus
    addresses = df['Address'].tolist()
    addresses.append(query1)  # Append queries for vectorization
    addresses.append(query2)

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(addresses)

    # Compute Cosine Similarity for both queries
    sim_query1 = cosine_similarity(tfidf_matrix[-2], tfidf_matrix[:-2])[0]
    sim_query2 = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-2])[0]

    # Filter addresses where both queries match with at least 0.3 similarity
    matched_indices = [idx for idx in range(len(sim_query1)) if sim_query1[idx] > 0.3 and sim_query2[idx] > 0.3]

    # Filter by Pincode
    if pincodes:
        matched_indices = [idx for idx in matched_indices if str(df.iloc[idx]['Pincode']) in pincodes]

    # Return only relevant addresses (keeping original data format)
    return df.iloc[matched_indices]

# Clustering Addresses with DBSCAN
def cluster_addresses(df):
    """Clusters addresses based on text similarity using DBSCAN."""
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Address'])

    # DBSCAN clustering based on cosine similarity
    dbscan = DBSCAN(metric="cosine", eps=0.3, min_samples=2)
    clusters = dbscan.fit_predict(tfidf_matrix.toarray())

    # Assign cluster labels
    df["Cluster"] = clusters
    return df

# Streamlit UI
st.title("🔍 Address Filtering & Clustering System")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)  # Clean addresses before processing

    # User Input
    query1 = st.text_input("✍️ Enter First Keyword:")
    query2 = st.text_input("✍️ Enter Second Keyword:")
    pincode_input = st.text_input("📍 Enter up to 2 Pincodes (comma-separated):")

    if st.button("🔎 Search & Cluster"):
        pincodes = [p.strip() for p in pincode_input.split(",") if p.strip().isdigit()][:2]  # Allow max 2 pincodes
        result = search_addresses(df, query1, query2, pincodes)
        
        if not result.empty:
            # Apply clustering
            clustered_result = cluster_addresses(result)
            match_count = len(clustered_result)
            
            st.success(f"✅ {match_count} related addresses found and clustered!")
            st.dataframe(clustered_result)

            # Download CSV
            csv = clustered_result.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Clustered Data", csv, "clustered_addresses.csv", "text/csv")
        else:
            st.warning(f"❌ No results found for '{query1}' & '{query2}' with Pincode(s): {', '.join(pincodes)}.")
