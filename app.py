import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer

# Load dataset
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)

# Preprocess Address Column
def clean_address(address):
    address = str(address).strip()
    address = re.sub(r'[^a-zA-Z0-9\s]', '', address)  # Remove special characters
    address = re.sub(r'\s+', ' ', address)  # Normalize spaces
    common_replacements = {
        'rd': 'road', 'st': 'street', 'ave': 'avenue', 'blvd': 'boulevard',
        'svrd': 'sv road', 'mg rd': 'mg road', 'jdbc': 'junction'
    }
    for key, val in common_replacements.items():
        address = re.sub(fr'\b{key}\b', val, address, flags=re.IGNORECASE)
    return address

# Improved Search Function
def search_addresses(df, query, threshold=90):
    query = query.strip()
    
    # **1. Try Exact Match First**
    exact_matches = df[df['Address'].str.contains(re.escape(query), regex=True, case=False, na=False)]
    if not exact_matches.empty:
        return exact_matches

    # **2. Use Fuzzy Matching for Partial Matches**
    fuzzy_matches = []
    for index, address in df['Address'].items():
        match_score = process.extract(query, [address], limit=1)  # Get top match
        if match_score and match_score[0][1] >= threshold:
            fuzzy_matches.append(index)
    
    return df.loc[fuzzy_matches] if fuzzy_matches else pd.DataFrame(columns=df.columns)  # Ensure DataFrame output

# Streamlit UI
st.title(" Address Filtering System 🔎")

# File Upload
uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)

    # User Input
    query = st.text_input("🔍 Enter a keyword to search for related addresses:")
    threshold = st.slider("Fuzzy Match Threshold", 50, 100, 90)

    if st.button("Search"):
        result = search_addresses(df, query, threshold)
        match_count = len(result)

        if match_count > 0:
            st.success(f"✅ {match_count} addresses found for '{query}':")
            st.dataframe(result)
            # Download CSV
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results", csv, "filtered_addresses.csv", "text/csv")
        else:
            st.warning(f"❌ No results found for '{query}'.")
