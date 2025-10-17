#!/usr/bin/env python3
"""
Google Books Reconciliation Script
Finds books without ISBNs, queries Google Books API, validates with Gemini, and updates records.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from google import genai
from google.genai import types


def load_books():
    """Load books from JSON file."""
    with open('data/books_by_title.json', 'r') as f:
        return json.load(f)


def save_books(books):
    """Save books to JSON file."""
    with open('data/books_by_title.json', 'w') as f:
        json.dump(books, f, indent=2)


def clean_title(title):
    """Remove parenthetical text from title."""
    return re.sub(r'\s*\([^)]*\)', '', title).strip()


def get_author_lastname(author):
    """Extract last name from author string (format: 'Lastname, Firstname')."""
    if ',' in author:
        return author.split(',')[0].strip()
    return author.strip()


def query_google_books(title, author):
    """Query Google Books API for a book."""
    clean_t = clean_title(title)
    author_last = get_author_lastname(author)

    print(f"  [VERBOSE] Cleaned title: '{clean_t}'")
    print(f"  [VERBOSE] Author last name: '{author_last}'")

    query = f"intitle:{clean_t}+inauthor:{author_last}"
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}"

    print(f"  [VERBOSE] Query URL: {url}")

    try:
        print(f"  [VERBOSE] Making request to Google Books API...")
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print(f"  [VERBOSE] Response received: {data.get('totalItems', 0)} items found")
            return data
    except Exception as e:
        print(f"  [ERROR] Error querying Google Books: {e}")
        return None


def validate_with_gemini(google_books_data, title, author):
    """Use Gemini to validate if the Google Books result is a good match."""
    print(f"  [VERBOSE] Validating with Gemini AI...")

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt = f"""Is this data result from google books:
{json.dumps(google_books_data, indent=2)}

A good match for this record:
{title} by {author}

Return JSON: {{"match":true/false, "reason_why":"short 1 sentence why or why not"}}"""

    print(f"  [VERBOSE] Sending prompt to Gemini (length: {len(prompt)} chars)")

    model = "gemini-flash-latest"
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=0,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
        response_mime_type="application/json",
    )

    try:
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text

        print(f"  [VERBOSE] Gemini response received: {response_text}")
        return json.loads(response_text)
    except Exception as e:
        print(f"  [ERROR] Error validating with Gemini: {e}")
        return None


def update_book_metadata(book_data, google_book_item, gemini_validation):
    """Update book metadata with information from Google Books."""
    print(f"  [VERBOSE] Updating book metadata...")

    volume_info = google_book_item.get('volumeInfo', {})

    # Extract ISBNs
    isbns = []
    for identifier in volume_info.get('industryIdentifiers', []):
        isbn = identifier.get('identifier')
        if isbn:
            isbns.append(isbn)

    print(f"  [VERBOSE] Extracted ISBNs: {isbns}")

    # Update metadata
    if isbns:
        book_data['metadata']['isbns'] = isbns
        print(f"  [VERBOSE] Updated ISBNs field")

    # Optionally update other fields if they're missing
    if not book_data['metadata'].get('publisher'):
        publisher = volume_info.get('publisher', '')
        book_data['metadata']['publisher'] = publisher
        if publisher:
            print(f"  [VERBOSE] Added publisher: {publisher}")

    if not book_data['metadata'].get('publishedDate'):
        pub_date = volume_info.get('publishedDate', '')
        book_data['metadata']['publishedDate'] = pub_date
        if pub_date:
            print(f"  [VERBOSE] Added published date: {pub_date}")

    if not book_data['metadata'].get('description'):
        description = volume_info.get('description', '')
        book_data['metadata']['description'] = description
        if description:
            print(f"  [VERBOSE] Added description ({len(description)} chars)")

    # Store Gemini validation response
    book_data['metadata']['gemini_validation'] = gemini_validation
    print(f"  [VERBOSE] Stored Gemini validation response")

    return book_data


def main():
    """Main execution function."""
    print("[VERBOSE] Starting Google Books reconciliation script...")
    print("[VERBOSE] Loading books from data/books_by_title.json...")

    books = load_books()
    total_books = len(books)
    print(f"[VERBOSE] Loaded {total_books} books total")

    # Count books without ISBNs
    books_without_isbns = 0
    for book_data in books.values():
        metadata = book_data.get('metadata', {})
        isbns = metadata.get('isbns', [])
        if not isbns or len(isbns) == 0:
            books_without_isbns += 1

    print(f"[VERBOSE] Found {books_without_isbns} books without ISBNs")
    print("\n" + "="*80 + "\n")

    processed_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for book_id, book_data in books.items():
        metadata = book_data.get('metadata', {})
        isbns = metadata.get('isbns', [])

        # Skip if already has ISBNs
        if isbns and len(isbns) > 0:
            continue

        title = metadata.get('title', '')
        author = metadata.get('author', '')

        if not title or not author:
            print(f"[SKIP] Book ID {book_id}: missing title or author")
            skipped_count += 1
            continue

        processed_count += 1
        print(f"\n[{processed_count}/{books_without_isbns}] Processing Book ID: {book_id}")
        print(f"  Title: {title}")
        print(f"  Author: {author}")

        # Query Google Books
        google_data = query_google_books(title, author)
        if not google_data or google_data.get('totalItems', 0) == 0:
            print(f"  [RESULT] No results found in Google Books")
            failed_count += 1
            continue

        # Get first result
        first_item = google_data['items'][0]
        google_title = first_item.get('volumeInfo', {}).get('title', 'N/A')
        google_authors = first_item.get('volumeInfo', {}).get('authors', [])
        print(f"  [VERBOSE] First Google Books result:")
        print(f"    - Title: {google_title}")
        print(f"    - Authors: {', '.join(google_authors)}")

        # Validate with Gemini
        validation = validate_with_gemini(google_data, title, author)
        if not validation:
            print(f"  [RESULT] Failed to validate with Gemini")
            failed_count += 1
            continue

        print(f"  [GEMINI] Match: {validation.get('match')}")
        print(f"  [GEMINI] Reason: {validation.get('reason_why')}")

        if validation.get('match'):
            # Update book metadata
            book_data = update_book_metadata(book_data, first_item, validation)
            books[book_id] = book_data
            print(f"  [SUCCESS] Updated with ISBNs: {book_data['metadata']['isbns']}")
            updated_count += 1

            # Save after each successful update
            print(f"  [VERBOSE] Saving to disk...")
            save_books(books)
            print(f"  [VERBOSE] Save complete")
        else:
            print(f"  [RESULT] Not a match - skipping update")
            failed_count += 1

        # Rate limiting - be nice to the APIs
        print(f"  [VERBOSE] Waiting 1 second before next request...")
        time.sleep(1)
        print("\n" + "-"*80)

    print("\n" + "="*80)
    print("[COMPLETE] Reconciliation complete!")
    print(f"  Total books: {total_books}")
    print(f"  Books without ISBNs: {books_without_isbns}")
    print(f"  Processed: {processed_count}")
    print(f"  Successfully updated: {updated_count}")
    print(f"  Failed/No match: {failed_count}")
    print(f"  Skipped (missing data): {skipped_count}")
    print("="*80)


if __name__ == "__main__":
    main()
