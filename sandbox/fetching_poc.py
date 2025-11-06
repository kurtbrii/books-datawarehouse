import requests
import json

# Test books from your CSV
test_books = [
    {"title": "A Court of Wings and Ruin", "author": "Sarah J. Maas"},
    {"title": "Turtles All the Way Down", "author": "John Green"},
]


def test_open_library(title, author):
    """Test Open Library API"""
    print(f"\n{'=' * 60}")
    print(f"OPEN LIBRARY - {title} by {author}")
    print("=" * 60)

    # Format query: replace spaces with +
    query = f"{title} {author}".replace(" ", "+")
    url = f"https://openlibrary.org/search.json?q={query}&limit=1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Print full response
        print(json.dumps(data, indent=2))

    #     # Check if we got results
    #     if data.get("numFound", 0) > 0:
    #         book = data["docs"][0]
    #         print(f"\n✓ Found book!")
    #         print(f"  - Title: {book.get('title')}")
    #         print(f"  - Author: {book.get('author_name')}")
    #         print(f"  - First publish year: {book.get('first_publish_year')}")
    #         print(f"  - Edition count: {book.get('edition_count')}")
    #         print(
    #             f"  - ISBN: {book.get('isbn', ['N/A'])[0] if book.get('isbn') else 'N/A'}"
    #         )
    #     else:
    #         print("✗ No results found")

    except Exception as e:
        print(f"✗ Error: {e}")


def test_google_books(title, author):
    """Test Google Books API"""
    print(f"\n{'=' * 60}")
    print(f"GOOGLE BOOKS - {title} by {author}")
    print("=" * 60)

    # Format query
    query = f"{title} {author}".replace(" ", "+")
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Print full response
        print(json.dumps(data, indent=2))

        # Check if we got results
        # if data.get("totalItems", 0) > 0:
        #     book = data["items"][0]["volumeInfo"]
        #     print(f"\n✓ Found book!")
        #     print(f"  - Title: {book.get('title')}")
        #     print(f"  - Authors: {book.get('authors')}")
        #     print(f"  - Publisher: {book.get('publisher')}")
        #     print(f"  - Published Date: {book.get('publishedDate')}")
        #     print(f"  - Page Count: {book.get('pageCount')}")
        #     print(f"  - Average Rating: {book.get('averageRating', 'N/A')}")
        #     print(f"  - Ratings Count: {book.get('ratingsCount', 'N/A')}")
        #     print(f"  - Categories: {book.get('categories')}")
        # else:
        #     print("✗ No results found")

    except Exception as e:
        print(f"✗ Error: {e}")


# Run tests
if __name__ == "__main__":
    print("Starting API POC Tests...")
    print("=" * 60)

    for book in test_books:
        test_open_library(book["title"], book["author"])
        print("\n" + "=" * 60 + "\n")
        # test_google_books(book["title"], book["author"])
        print("\n" + "=" * 60 + "\n")

    # print("POC Tests Complete!")
    # print("\nNext steps:")
    # print("1. Review the JSON responses above")
    # print("2. Verify all needed fields are present")
    # print("3. Note any missing or inconsistent data")
    # print("4. Decide if APIs meet your requirements")
