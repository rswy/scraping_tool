import json
import pandas as pd
from collections import Counter
import re
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np # Import numpy for NaN

# Import NLTK and download stopwords if not already present
import nltk
try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')
from nltk.corpus import stopwords


# 1. Import all settings from our configuration file
import config

# Set a style for the plots for better aesthetics
sns.set_style("whitegrid")

# Load the JSON data from the uploaded file
file_path = config.OUTPUT_FILENAME
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Convert the list of dictionaries to a pandas DataFrame
df = pd.DataFrame(data)

# --- Data Cleaning and Preprocessing ---
df['price_numeric'] = df['price'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
df['price_numeric'] = pd.to_numeric(df['price_numeric'], errors='coerce')

# Convert 'num_reviews' to numeric
df['num_reviews_numeric'] = df['num_reviews'].str.replace(',', '').astype(int)

# Convert 'rating' to numeric
df['rating_numeric'] = df['rating'].astype(float)

# --- Data Analysis ---

print("--- Data Overview ---")
print(df.head())
print("\n--- Basic Statistics for Numeric Columns ---")
print(df[['price_numeric', 'rating_numeric', 'num_reviews_numeric']].describe())

# 1. Top Rated Products
print("\n--- Top 5 Highest Rated Products (by average rating) ---")
top_rated_products = df.sort_values(by='rating_numeric', ascending=False).head(5)
print(top_rated_products[['product_name', 'rating_numeric', 'num_reviews_numeric']])

# 2. Most Reviewed Products
print("\n--- Top 5 Most Reviewed Products ---")
most_reviewed_products = df.sort_values(by='num_reviews_numeric', ascending=False).head(5)
print(most_reviewed_products[['product_name', 'num_reviews_numeric', 'rating_numeric']])


# 3. Improved Product Categorization using a dictionary mapping
# Initialize a new column to store the determined category for each product
df['product_category'] = 'Other'

# Define categorization logic based on keywords in a dictionary
category_keywords = {
    'Location Trackers': ['airtag'],
    'Audio Accessories': ['airpods', 'earbuds', 'headphones', 'jbl', 'soundcore', 'tozo', 'trausi', 'beribes', 'pocbuds', 'kurdene', 'beats'],
    'Streaming Devices': ['fire tv stick', 'roku'],
    'Power & Connectivity': ['power strip', 'surge protector', 'charger', 'usb c hub', 'wall charger', 'extension cord', 'adapter'],
    'Smart Home Devices': ['echo', 'smart plug', 'alexa'],
    'Tablets': ['ipad', 'tablet'],
    'E-readers': ['kindle'],
    'TV Mounts': ['tv wall mount', 'mounting dream', 'pipishell', 'amazon basics full motion'],
    'Cameras & Security': ['camera', 'blink outdoor', 'dash cam', 'ring battery doorbell'],
    'Remotes': ['remote control', 'remote for roku', 'remote for samsung'],
    'Televisions': ['vizio', 'insignia', 'tv', 'smart tv'],
    'Cable Management': ['zip ties', 'cable ties'],
    'Optics': ['binoculars']
}

# Assign categories based on keywords
for index, row in df.iterrows():
    name_lower = row['product_name'].lower()
    found_category = False
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in name_lower:
                df.at[index, 'product_category'] = category
                found_category = True
                break # Found a category, move to next product
        if found_category:
            break

product_categories_counts = df['product_category'].value_counts()

print("\n--- Product Categories Distribution ---")
print(product_categories_counts)

# 4. Analyze common words in reviews (using NLTK stopwords)
all_reviews = []
# Ensure 'reviews' column is treated as list and drop NaNs
for reviews_list in df['reviews'].dropna():
    if isinstance(reviews_list, list): # Check if it's actually a list before extending
        all_reviews.extend(reviews_list)

# Join all reviews into a single string
full_text = " ".join(all_reviews).lower()

# Remove punctuation and split into words
words = re.findall(r'\b\w+\b', full_text)

# Get NLTK English stopwords and extend with custom review-specific stopwords
nltk_stopwords = set(stopwords.words('english'))
custom_stopwords = set([
    "product", "item", "use", "using", "buy", "bought", "amazon", "day", "days", "months", "year", "years",
    "get", "like", "just", "even", "amp", "really", "much", "one", "can", "see", "think", "also", "way",
    "need", "time", "back", "etc", "etc.", "got", "did", "my", "your", "they", "we", "us", "i", "it", "so"
])
all_stopwords = nltk_stopwords.union(custom_stopwords)


filtered_words = [word for word in words if word not in all_stopwords and len(word) > 2]

# Get the most common words
word_counts = Counter(filtered_words)

print("\n--- Top 20 Most Common Words in Reviews (excluding stopwords) ---")
for word, count in word_counts.most_common(20):
    print(f"{word}: {count}")

# 5. Sentiment analysis (basic keyword spotting for positive/negative sentiment)
positive_keywords = ['great', 'amazing', 'love', 'excellent', 'fantastic', 'impressed', 'seamless', 'convenient', 'happy', 'good', 'perfect', 'reliable', 'worth', 'smooth', 'crisp', 'clear', 'best', 'easy', 'strong', 'solid', 'recommend']
negative_keywords = ['issue', 'problem', 'flaw', 'slow', 'disappointed', 'lag', 'uncomfortable', 'struggle', 'annoying', 'drain', 'muffled', 'distortion', 'overheating', 'buggy', 'weak', 'hard', 'stuck', 'difficult', 'noise', 'bad']

sentiment_scores = []
# Add a product_id or similar unique identifier to link scores back to original df if needed, though not strictly necessary here as we append in order
for reviews_list in df['reviews'].dropna():
    product_sentiment = 0
    for review in reviews_list:
        review_lower = review.lower()
        for keyword in positive_keywords:
            product_sentiment += review_lower.count(keyword)
        for keyword in negative_keywords:
            product_sentiment -= review_lower.count(keyword)
    sentiment_scores.append(product_sentiment)

df['sentiment_score'] = pd.Series(sentiment_scores)

print("\n--- Products with Highest Positive Sentiment (Top 5) ---")
top_sentiment_products = df.sort_values(by='sentiment_score', ascending=False).head(5)
print(top_sentiment_products[['product_name', 'rating_numeric', 'num_reviews_numeric', 'sentiment_score']])

print("\n--- Products with Lowest Sentiment (Top 5) ---")
lowest_sentiment_products = df.sort_values(by='sentiment_score', ascending=True).head(5)
print(lowest_sentiment_products[['product_name', 'rating_numeric', 'num_reviews_numeric', 'sentiment_score']])

# --- Visualizations ---

# Visualization 1: Product Categories Distribution (for Insight 1)
plt.figure(figsize=(10, 7))
sns.barplot(x=product_categories_counts.values, y=product_categories_counts.index, palette='viridis')
plt.title('Distribution of Bestselling Product Categories')
plt.xlabel('Number of Products')
plt.ylabel('Product Category')
plt.tight_layout()
plt.savefig('./data_analysis/product_categories_distribution.png')
plt.close() # Close the plot to free memory

# Visualization 2: Total Reviews by Product Category (for Insight 2)
# Group by category and sum the number of reviews
reviews_by_category = df.groupby('product_category')['num_reviews_numeric'].sum().sort_values(ascending=False)

plt.figure(figsize=(12, 8))
sns.barplot(x=reviews_by_category.values, y=reviews_by_category.index, palette='magma')
plt.title('Total Number of Reviews by Product Category')
plt.xlabel('Total Number of Reviews (Log Scale)')
plt.ylabel('Product Category')
plt.xscale('log') # Use log scale due to large differences in review counts
plt.tight_layout()
plt.savefig('./data_analysis/total_reviews_by_category.png')
plt.close() # Close the plot

# Visualization 3: Top 20 Most Common Words in Reviews (for Insight 3)
top_20_words = word_counts.most_common(20)
words_df = pd.DataFrame(top_20_words, columns=['Word', 'Count'])

plt.figure(figsize=(12, 8))
sns.barplot(x='Count', y='Word', data=words_df, palette='cividis')
plt.title('Top 20 Most Common Words in Customer Reviews')
plt.xlabel('Frequency')
plt.ylabel('Word')
plt.tight_layout()
plt.savefig('./data_analysis/top_common_words_in_reviews.png')
plt.close() # Close the plot

print("\nVisualizations saved as: product_categories_distribution.png, total_reviews_by_category.png, and top_common_words_in_reviews.png")