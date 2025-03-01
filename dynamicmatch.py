import pandas as pd
from rapidfuzz import fuzz, process

# Load the CSV file
df = pd.read_csv("D:/data for address/master.csv")  # Ensure 'Address' column exists

# **Step 1: Extract Unique Words from Addresses**
def extract_unique_keywords(df):
    """Extract unique words from the address column to create a keyword set."""
    unique_words = set()
    for address in df["Address"].dropna():
        words = str(address).lower().split()  # Convert to lowercase and split into words
        unique_words.update(words)
    return unique_words

# **Step 2: Find Matching Addresses Based on Multi-Word Query**
def find_matching_addresses(search_terms, df, threshold=70):
    """
    Match addresses dynamically based on multiple search terms.

    Parameters:
    - search_terms: Full search query as a phrase or separate words.
    - df: DataFrame containing addresses.
    - threshold: Similarity threshold (default: 70%).

    Returns:
    - DataFrame of matched addresses with similarity scores.
    """
    matches = []
    search_phrase = " ".join(search_terms).lower()  # Join search terms into a single string

    for address in df["Address"].dropna():
        address_lower = str(address).lower()

        # Use fuzz.token_sort_ratio to match entire phrases better
        similarity = fuzz.token_sort_ratio(search_phrase, address_lower)

        if similarity >= threshold:
            matches.append((address, similarity))

    # Convert to DataFrame and sort by similarity score
    matched_df = pd.DataFrame(matches, columns=["Matched Address", "Similarity"]).sort_values(by="Similarity", ascending=False)

    return matched_df

# **Step 3: Extract Keywords & Get User Search Input**
keyword_list = extract_unique_keywords(df)
print("Extracted Keywords:", keyword_list)

# **Step 4: Get Search Terms (Multi-Word Support)**
search_input = input("Enter search phrase (e.g., 'shah industrial andheri east'): ")
search_keywords = search_input.split()  # Takes full user input

# **Step 5: Perform Matching**
matched_df = find_matching_addresses(search_keywords, df)

# **Step 6: Save Matched Addresses to CSV**
matched_df.to_csv("matched_addresses.csv", index=False)
print(f"Matched addresses saved to 'matched_addresses.csv'")

# **Step 7: Display Top Matches**
print(matched_df.head(10))  # Show first 10 results
