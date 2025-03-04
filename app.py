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
    address = re.sub(r'[^a-zA-Z0-9\s,]', '', address)  # Remove special characters (allow commas)
    address = re.sub(r'\s+', ' ', address)  # Normalize spaces
    common_replacements = {
        'rd': 'road', 'st': 'street', 'ave': 'avenue', 'blvd': 'boulevard',
        'svrd': 'sv road', 'mg rd': 'mg road', 'jdbc': 'junction'
    }
    for key, val in common_replacements.items():
        address = re.sub(fr'\b{key}\b', val, address, flags=re.IGNORECASE)
    return address

# Combined Search Function (Exact + Fuzzy)
def search_addresses(df, query, threshold=85):
    query = query.strip()
    query_words = [word.strip() for word in query.split(",")]  # Split by comma (multiple keywords)
    
    # **1. Find Exact Matches**
    exact_match_condition = df['Address'].apply(lambda addr: all(re.search(fr'\b{re.escape(word)}\b', addr, re.IGNORECASE) for word in query_words))
    exact_matches = df[exact_match_condition]

    # **2. Find Fuzzy Matches**
    fuzzy_matches = []
    for index, address in df['Address'].items():
        match_scores = [process.extractOne(word, [address]) for word in query_words]  # Get match for each word
        avg_score = sum(score[1] for score in match_scores if score) / len(match_scores)
        
        if avg_score >= threshold:
            fuzzy_matches.append(index)
    
    fuzzy_results = df.loc[fuzzy_matches] if fuzzy_matches else pd.DataFrame(columns=df.columns)
    
    # **3. Combine & Remove Duplicates**
    combined_results = pd.concat([exact_matches, fuzzy_results]).drop_duplicates()

    return combined_results  # Return merged results

# Streamlit UI
st.title("Address Filtering System 🔍")

# File Upload
uploaded_file = st.file_uploader("📂 Upload Excel file", type=['xlsx'])
if uploaded_file:
    df = load_data(uploaded_file)
    df['Address'] = df['Address'].apply(clean_address)

    # User Input
    query = st.text_input("Enter keywords (comma-separated) to search for related addresses:")
    threshold = st.slider("Fuzzy Match Threshold", 50, 100, 85)

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
