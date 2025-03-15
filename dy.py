import pandas as pd
import re
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load data
cluster_file = "D:/data for address/add/cluster.xlsx"
address_file = "D:/data for address/masterdata2025.xlsx"

 

df_cluster = pd.read_excel(cluster_file, sheet_name="Sheet1")
df_address = pd.read_excel(address_file)

# Create cluster dictionary
cluster_dict = {}
for _, row in df_cluster.iterrows():
    cluster_name = str(row["cluster_name"]).strip()
    pincode = str(row["pincode"]).strip()
    sub_areas = str(row["Keyword"]).strip().lower().split(",")  # Assuming sub-areas are comma-separated
    sub_areas = [area.strip() for area in sub_areas if area]
    cluster_dict[cluster_name] = {"areas": sub_areas, "pincode": pincode}

# Text Cleaning Function
def clean_text(text):
    text = str(text).lower().strip()
    text = re.sub(r"[^a-zA-Z0-9\s,]", "", text)  # Remove special characters
    text = re.sub(r"\s+", " ", text)  # Normalize spaces
    return text

# TF-IDF Preparation
corpus = [" ".join(data["areas"]) for data in cluster_dict.values()]
cluster_names = list(cluster_dict.keys())
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(corpus)

# Matching Function
def match_cluster(address, pincode):
    address = clean_text(address)
    best_match = "Unmatched"
    best_score = 0

    # Filter clusters by pincode
    filtered_clusters = {k: v for k, v in cluster_dict.items() if str(v["pincode"]) == str(pincode)}
    if not filtered_clusters:
        filtered_clusters = cluster_dict  # If no exact pincode match, consider all clusters

    # TF-IDF Similarity
    address_vector = vectorizer.transform([address])
    similarity_scores = cosine_similarity(address_vector, tfidf_matrix)[0]
    
    best_tfidf_idx = similarity_scores.argmax()
    best_tfidf_score = similarity_scores[best_tfidf_idx]
    best_cluster_tfidf = cluster_names[best_tfidf_idx] if best_tfidf_score > 0.3 else None

    # Fuzzy Matching
    for cluster, data in filtered_clusters.items():
        for area in data["areas"]:
            area_clean = clean_text(area)
            fuzzy_score = fuzz.token_set_ratio(address, area_clean)
            if fuzzy_score > best_score:
                best_score = fuzzy_score
                best_match = cluster

    # Decision Logic
    if best_score > 60:
        return best_match
    elif best_tfidf_score > 0.3:
        return best_cluster_tfidf
    else:
        return "Unmatched"

# Apply Matching to Address Data
df_address["Cluster"] = df_address.apply(lambda row: match_cluster(str(row["Address"]), str(row["Pincode"])), axis=1)

# Save the output
output_file = "clustered_addresses.xlsx"
df_address.to_excel(output_file, index=False)
print(f"✅ Clustering complete! Results saved to {output_file}")
