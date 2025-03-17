import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Page Configuration
st.set_page_config(page_title="Address Clustering System", page_icon="📍", layout="wide")


# Function to clean text
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"(\d+)([a-zA-Z])", r"\1 \2", text)  # Space between numbers and letters
    text = re.sub(r"([a-zA-Z])(\d+)", r"\1 \2", text)  # Space between letters and numbers
    text = re.sub(r"[^a-zA-Z0-9\s,]", "", text)  # Remove special characters
    text = re.sub(r"\s+", " ", text)  # Normalize spaces
    return text

# Function to load data
@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)
#do the changes
# Load reference clusters
def load_clusters(file):
    xls = pd.ExcelFile(file)
    df_ref = pd.read_excel(xls, sheet_name="Sheet1")
    
    cluster_dict = {}
    for _, row in df_ref.iterrows():
        keyword = str(row["Keyword"]).strip()
        pincode = str(row["pincode"]).strip()
        
        if ":" in keyword and "[" in keyword:
            cluster_name = keyword.split(":")[0].strip()
            sub_areas = keyword.split("[")[-1].replace("]", "").replace(";", ",").split(",")
            sub_areas = [clean_text(area) for area in sub_areas]
            cluster_dict[cluster_name] = {"areas": sub_areas, "pincode": pincode}
    return cluster_dict

# Match Address to Cluster
def match_cluster(address, pincode, cluster_dict, vectorizer, tfidf_matrix, cluster_names):
    address = clean_text(address)
    address_tokens = set(address.split())

    best_match = None
    best_score = 0

    # Step 1: Filter clusters by pincode
    filtered_clusters = {k: v for k, v in cluster_dict.items() if str(v["pincode"]) == str(pincode)}
    
    if not filtered_clusters:
        return "Unmatched"

    # Step 2: TF-IDF Similarity
    address_vector = vectorizer.transform([address])
    similarity_scores = cosine_similarity(address_vector, tfidf_matrix)[0]

    best_tfidf_idx = similarity_scores.argmax()
    best_tfidf_score = similarity_scores[best_tfidf_idx]
    best_cluster_tfidf = cluster_names[best_tfidf_idx] if best_tfidf_score > 0.35 else None

    # Step 3: Fuzzy Matching
    for cluster, data in filtered_clusters.items():
        for area in data["areas"]:
            cleaned_area = clean_text(area)
            area_tokens = set(cleaned_area.split())

            if area_tokens & address_tokens:
                return cluster

            fuzzy_score = fuzz.token_set_ratio(address, cleaned_area)
            if fuzzy_score > best_score:
                best_score = fuzzy_score
                best_match = cluster

    if best_score > 60:
        return best_match
    elif best_tfidf_score > 0.35:
        return best_cluster_tfidf
    else:
        return "Unmatched"

# Streamlit UI
st.title("📍 Address Clustering System")
st.markdown("Upload your files to process addresses and match them to clusters.")

# File Uploads
col1, col2 = st.columns(2)
with col1:
    cluster_file = st.file_uploader("📂 Upload Cluster File (Excel)", type=['xlsx'])
with col2:
    address_file = st.file_uploader("📂 Upload Address File (Excel)", type=['xlsx'])

  # Horizontal line for better UI separation

# Processing files
if cluster_file and address_file:
    status = st.empty()  # Create a placeholder for status messages
    status.info("⏳ Processing data... Please wait.")

    cluster_dict = load_clusters(cluster_file)
    df_new = load_data(address_file)

    # Prepare TF-IDF
    corpus = [" ".join(data["areas"]) for data in cluster_dict.values()]
    cluster_names = list(cluster_dict.keys())
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Apply clustering
    df_new["Cluster"] = df_new.apply(lambda row: match_cluster(str(row["Address"]), str(row["Pincode"]), 
                                                                cluster_dict, vectorizer, tfidf_matrix, cluster_names), axis=1)

    status.empty()  # Clear the "Processing..." message
    st.success("✅ Address clustering completed!")  # Show success message
    st.dataframe(df_new)

    # Download processed file
    output_file = df_new.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Clustered Data", output_file, "clustered_addresses.csv", "text/csv")

# Footer Section
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 10px; font-size: 14px;'>
        Created by <b>Siddhi Patade</b> | © 2025 Address Clustering System
    </div>
    """,
    unsafe_allow_html=True
)
