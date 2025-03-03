import pandas as pd
import re
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer

# Load dataset
df = pd.read_excel('D:/data for address/masterdata2025.xlsx')

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
        address = re.sub(fr'\b{key}\b', val, address)
    return address

df['Address'] = df['Address'].apply(clean_address)

# Extract Keywords including city and pincode
def extract_keywords(addresses, cities, pincodes):
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    vectorizer.fit_transform(addresses)
    address_keywords = set(vectorizer.get_feature_names_out())

    # Combine with city names and pincodes
    all_keywords = address_keywords.union(set(cities)).union(set(pincodes))
    return sorted(all_keywords)

# Extract distinct cities and pincodes
cities = df['R_City'].astype(str).unique()
pincodes = df['Pincode'].astype(str).unique()

keywords = extract_keywords(df['Address'], cities, pincodes)

# Save extracted keywords
keywords_df = pd.DataFrame(keywords, columns=['Keyword'])
keywords_df.to_csv('keywords.csv', index=False)

# Improved Search Function
def search_addresses(df, query, threshold=90):
    exact_matches = df[df['Address'].str.contains(fr'\b{re.escape(query)}\b', regex=True, na=False)]

    if not exact_matches.empty:
        return exact_matches

    # If no exact match, apply fuzzy matching with a high threshold
    matches = []
    for address in df['Address']:
        match_score = process.extractOne(query, [address])
        if match_score and match_score[1] >= threshold:
            matches.append(address)
    return df[df['Address'].isin(matches)]

# Example input query
query = input("Enter a keyword to search for related addresses: ")
result = search_addresses(df, query)

# Save result
result.to_csv('filtered_addresses.csv', index=False)

print("Filtered addresses saved to filtered_addresses.csv")

# Display top 10 matches
print(result.head(10))