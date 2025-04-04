import streamlit as st
import pandas as pd
import re
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import streamlit as st
import base64

# Page Configuration
st.set_page_config(page_title="Address Processing System", page_icon="namalogo.webp", layout="wide")

# Display logo and title in the same line
col1, col2 = st.columns([0.09, 0.9])
with col1:
    st.image("namalogo.webp", width=70)  # Use a relative path

with col2:
    st.markdown(
        "<h1 style='font-size: 32px; color: #0047AB;'>Namaskar Distribution Solutions Pvt Ltd</h1>", 
        unsafe_allow_html=True
    )


# Function to clean text
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"(\d+)([a-zA-Z])", r"\1 \2", text)  # Space between numbers and letters
    text = re.sub(r"([a-zA-Z])(\d+)", r"\1 \2", text)  # Space between letters and numbers
    text = re.sub(r"[^a-zA-Z0-9\s,]", "", text)  # Remove special characters
    text = re.sub(r"\s+", " ", text)  # Normalize spaces
    return text

# Function to load data with format handling
@st.cache_data
def load_data(uploaded_file):
    file_extension = uploaded_file.name.split(".")[-1].lower()
    if file_extension == "csv":
        return pd.read_csv(uploaded_file, encoding="ISO-8859-1")  # Handling encoding issues
    elif file_extension in ["xls", "xlsx"]:
        return pd.read_excel(uploaded_file, engine="openpyxl")  # Ensures proper Excel handling
    else:
        st.error("❌ Unsupported file format. Please upload CSV or Excel files only.")
        return None

# Load reference clusters
def load_clusters(file):
    df_ref = load_data(file)
    if df_ref is None:
        return None
    
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
st.title(" Address Processing System")
tabs = st.tabs([" Address Cluster", " Search in Clustered Data", " Address Filtering"])

# Address Clustering Tab
with tabs[0]:
    st.subheader("📄 Address Cluster")
    col1, col2 = st.columns(2)
    with col1:
        cluster_file = st.file_uploader("📂 Upload Cluster File", type=['xlsx', 'csv'], key='cluster')
    with col2:
        address_file = st.file_uploader("📂 Upload Address File", type=['xlsx', 'csv'], key='address')
    
    if cluster_file and address_file:
        status = st.empty()
        status.info("⏳ Processing data... Please wait.")
        
        cluster_dict = load_clusters(cluster_file)
        df_new = load_data(address_file)
        
        if cluster_dict and df_new is not None:
            corpus = [" ".join(data["areas"]) for data in cluster_dict.values()]
            cluster_names = list(cluster_dict.keys())
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            df_new["Cluster"] = df_new.apply(lambda row: match_cluster(str(row["Address"]), str(row["Pincode"]),
                                                                        cluster_dict, vectorizer, tfidf_matrix, cluster_names), axis=1)
            status.empty()
            st.success("✅ Address clustering completed!")
            st.dataframe(df_new)
            
            output_file = df_new.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Clustered Data", output_file, "clustered_addresses.csv", "text/csv")

# Search in Clustered Data Tab
with tabs[1]:
    st.subheader("🔎 Search in Clustered Data")
    uploaded_clustered_file = st.file_uploader("📂 Upload Clustered File", type=['csv', 'xlsx'], key='clustered_search')
    
    if uploaded_clustered_file:
        df_clustered = load_data(uploaded_clustered_file)
        if df_clustered is not None:
            df_clustered['Address'] = df_clustered['Address'].apply(clean_text)
            cluster_names = df_clustered['Cluster'].unique().tolist()
            
            st.write("### Available Clusters:")
            st.write(", ".join(cluster_names))
            
            query = st.text_input("✍️ Enter Cluster Name(s) (comma-separated):")
            
            if st.button("🔎 Search", key='search_clustered'):
                queries = [q.strip() for q in query.split(",") if q.strip()]
                
                if queries:
                    df_result = df_clustered[df_clustered['Cluster'].str.contains("|".join(queries), case=False, na=False)]
                    
                    if not df_result.empty:
                        st.success(f"✅ {len(df_result)} matching addresses found!")
                        st.dataframe(df_result)
                        csv = df_result.to_csv(index=False).encode('utf-8')
                        st.download_button("📥 Download Results", csv, f"clustered_addresses.csv", "text/csv")
                    else:
                        st.warning("❌ No matching addresses found.")
                else:
                    st.warning("⚠️ Please enter at least one cluster name.")


# Address Filtering Tab
with tabs[2]:
    st.subheader("📑 Address Filtering ")
    uploaded_file = st.file_uploader("📂 Upload Excel File", type=['xlsx', 'csv'], key='filter')
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            df['Address'] = df['Address'].apply(clean_text)
            query = st.text_input("✍️ Enter Keywords:")
            pincode_input = st.text_input("📍 Enter up to 2 Pincodes (comma-separated):")
            
            if st.button("🔎 Search", key='search'):
                pincodes = [p.strip() for p in pincode_input.split(",") if p.strip().isdigit()][:2]

                result = df[df['Address'].str.contains(query, case=False, na=False)]
                if not result.empty:
                    st.success(f"✅ {len(result)} related addresses found!")
                    st.dataframe(result)
                    csv = result.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Results", csv, f"{query}_cluster_addresses.csv", "text/csv")
                else:
                    st.warning("❌ No matching addresses found.")


# Footer Section
st.markdown("---")

st.markdown(
    """
    <div style='text-align: center; padding: 10px; font-size: 14px;'>
        <b>Namaskar Distribution Solutions Pvt Ltd</b> <br>
        Created by <b>Siddhi Patade</b> | © 2025 Address Clustering System
    </div>
    """,
    unsafe_allow_html=True
)