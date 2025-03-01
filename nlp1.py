import pandas as pd
import spacy
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Load the CSV file
df = pd.read_csv("D:/data for address/master.csv")  # Ensure 'Address' column exists
df.dropna(subset=["Address"], inplace=True)  # Remove null addresses

# **Fix Missing Spaces in Address Strings**
def fix_spacing(text):
    """Fix missing spaces in text caused by incorrect formatting."""
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # Add space between lowercase and uppercase letters

# **Step 1: Preprocess Addresses Using NLP**
def preprocess_text(text):
    """Cleans and normalizes an address using NLP while fixing spacing issues."""
    text = fix_spacing(text)  # Fix spacing issues first
    doc = nlp(text.lower().strip())  # Tokenize and lowercase
    processed_tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]  # Remove stopwords & lemmatize
    return " ".join(processed_tokens)

# Apply preprocessing to the Address column
df["clean_address"] = df["Address"].apply(preprocess_text)

# **Step 2: Match Addresses Using TF-IDF + Cosine Similarity**
def find_matching_addresses(search_query, df, top_n=10, min_similarity=0.50):
    """
    Finds the best matching addresses using TF-IDF and Cosine Similarity.

    Parameters:
    - search_query: User input query (full phrase)
    - df: DataFrame containing cleaned addresses
    - top_n: Number of top matches to consider (default: 10)
    - min_similarity: Minimum similarity score to keep results (default: 0.50)

    Returns:
    - DataFrame of matched addresses filtered by similarity threshold
    """
    # Preprocess search query
    search_query = preprocess_text(search_query)

    # Combine search query with address dataset
    all_texts = df["clean_address"].tolist() + [search_query]

    # Vectorize using TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Compute cosine similarity between search query and all addresses
    similarity_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

    # Add similarity scores to DataFrame
    df["Similarity"] = similarity_scores

    # Filter results based on similarity threshold (50% or more)
    matched_df = df[df["Similarity"] >= min_similarity].sort_values(by="Similarity", ascending=False)

    return matched_df[["Address", "Similarity"]]

# **Step 3: Get User Search Input**
search_input = input("Enter search phrase (e.g., 'shah industrial andheri east'): ")

# **Step 4: Perform NLP-Based Matching**
matched_df = find_matching_addresses(search_input, df)

# **Step 5: Save Filtered Matches to CSV (Only 50%+ Similarity)**
if not matched_df.empty:
    matched_df.to_csv("matched_addresses_nlp_fixed.csv", index=False)
    print(f"Matched addresses (50%+ similarity) saved to 'matched_addresses_nlp_fixed.csv'")
else:
    print("No matching addresses found with similarity above 50%.")

# **Step 6: Display Top Matches**
print(matched_df.head(10))  # Show first 10 results
