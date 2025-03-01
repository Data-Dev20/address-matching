import pandas as pd
from rapidfuzz import fuzz

# Load the CSV file
df = pd.read_csv("D:/data for address/master.csv")  # Ensure it has a column 'Address'

# **Step 1: Extract Unique Words from Addresses**
def extract_unique_keywords(df):
    """
    Extract unique words from the address column to create a keyword set.
    """
    unique_words = set()
    for address in df["Address"]:
        words = str(address).lower().split()  # Convert to lowercase and split into words
        unique_words.update(words)
    return unique_words

# **Step 2: Find Matching Addresses Based on Multiple Words**
def find_matching_addresses(search_terms, df, threshold=70):
    """
    Match addresses dynamically based on multiple search terms.

    Parameters:
    - search_terms: List of words/phrases to search for
    - df: DataFrame containing addresses
    - threshold: Similarity threshold (default: 70%)

    Returns:
    - DataFrame of matched addresses
    """
    matches = []
    
    for address in df["Address"]:
        address_lower = str(address).lower()
        match_score = 0
        
        for term in search_terms:
            similarity = fuzz.partial_ratio(term.lower(), address_lower)
            match_score += similarity
        
        avg_similarity = match_score / len(search_terms)  # Get the average similarity

        if avg_similarity >= threshold:
            matches.append(address)

    return pd.DataFrame(matches, columns=["Matched Address"])

# **Step 3: Extract Keywords & Get User Search Input**
keyword_list = extract_unique_keywords(df)
print("Extracted Keywords:", keyword_list)

# **Step 4: Get Search Terms (2-3 words)**
search_input = input("Enter search keywords (separated by spaces): ")
search_keywords = search_input.split()[:3]  # Limit to first 3 words

# **Step 5: Perform Matching**
matched_df = find_matching_addresses(search_keywords, df)

# **Step 6: Save Matched Addresses to CSV**
matched_df.to_csv("matched_addresses.csv", index=False)
print(f"Matched addresses saved to 'matched_addresses.csv'")

# **Step 7: Display Top Matches**
print(matched_df.head(10))  # Show first 10 results
