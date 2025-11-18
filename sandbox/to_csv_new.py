"""
This script fetches books from the Google Books API and writes them to a CSV file.
"""

import csv
import time
import requests

genres = [
    "fantasy fiction",
    "science fiction",
    "mystery fiction",
    "romance fiction",
    "literary fiction",
    "young adult fiction",
    "historical fiction",
    "horror fiction",
]

books = []

for genre in genres:
    query = f"subject:{genre}"
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&publishedDate=2025&maxResults=20"

    response = requests.get(url)
    data = response.json()

    for item in data.get("items", []):
        info = item["volumeInfo"]

        # Extract ISBN
        isbn = None
        for id in info.get("industryIdentifiers", []):
            if id["type"] == "ISBN_13":
                isbn = id["identifier"]
                break

        if isbn and info.get("title") and info.get("authors"):
            books.append(
                {"title": info["title"], "author": info["authors"][0], "isbn": isbn}
            )

    time.sleep(1)  # Rate limiting

# Write to CSV
with open("sandbox/curated_books.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "author", "isbn"])
    writer.writeheader()
    writer.writerows(books)

print(f"Generated CSV with {len(books)} books")
