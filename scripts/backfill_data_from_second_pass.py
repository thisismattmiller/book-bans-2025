#!/usr/bin/env python3
"""
Backfill missing metadata from refined_data_pass_two_enriched.csv into books_by_title.json.
Matches on title (removing parenthetical) and author.
"""

import json
import csv
import re
from pathlib import Path


def normalize_title(title):
    """Remove parenthetical from title for matching."""
    # Remove everything in parentheses at the end of the title
    return re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()


def normalize_author(author):
    """Normalize author name for matching."""
    return author.strip() if author else ""


def parse_isbns(isbn_string):
    """Parse ISBNs from CSV field."""
    if not isbn_string:
        return []
    # Split by pipe and filter out empty strings
    return [isbn.strip() for isbn in isbn_string.split('|') if isbn.strip()]


def main():
    # Paths
    base_dir = Path(__file__).parent.parent
    json_path = base_dir / 'data' / 'books_by_title.json'
    csv_path = base_dir / 'data' / 'refined_data_pass_two_enriched.csv'

    # Load JSON data
    print(f"Loading {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        books_data = json.load(f)

    # Find books with empty ISBNs
    books_needing_data = []
    for book_id, book in books_data.items():
        if 'metadata' in book and 'isbns' in book['metadata']:
            if len(book['metadata']['isbns']) == 0:
                books_needing_data.append({
                    'id': book_id,
                    'title': book['title'],
                    'title_normalized': normalize_title(book['title']),
                    'author': book['metadata'].get('author', ''),
                    'author_normalized': normalize_author(book['metadata'].get('author', ''))
                })

    print(f"Found {len(books_needing_data)} books with empty ISBNs")

    # Create lookup dictionary from CSV
    print(f"Loading {csv_path}...")
    csv_lookup = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('Title', '')
            author = row.get('Author', '')

            if title and author:
                title_norm = normalize_title(title)
                author_norm = normalize_author(author)
                key = (title_norm.lower(), author_norm.lower())

                # Store the row data
                csv_lookup[key] = {
                    'isbns': parse_isbns(row.get('ISBN', '')),
                    'title': title,
                    'author': author,
                    'description': row.get('Description', ''),
                    'language': row.get('Language', ''),
                    'page_count': row.get('Page Count', ''),
                    'subjects': row.get('Subjects', ''),
                    'genres': row.get('Genres', ''),
                }

    print(f"Loaded {len(csv_lookup)} entries from CSV")

    # Match and backfill
    matches_found = 0
    updated_books = 0

    for book in books_needing_data:
        key = (book['title_normalized'].lower(), book['author_normalized'].lower())

        if key in csv_lookup:
            matches_found += 1
            csv_data = csv_lookup[key]

            # Only update if CSV has ISBNs
            if csv_data['isbns']:
                book_id = book['id']
                books_data[book_id]['metadata']['isbns'] = csv_data['isbns']

                # Optionally update other metadata if empty
                metadata = books_data[book_id]['metadata']

                if csv_data.get('description') and not metadata.get('description'):
                    metadata['description'] = csv_data['description']

                if csv_data.get('language') and not metadata.get('language'):
                    metadata['language'] = csv_data['language']

                if csv_data.get('page_count') and not metadata.get('page_count'):
                    metadata['page_count'] = csv_data['page_count']

                if csv_data.get('subjects') and not metadata.get('subjects'):
                    metadata['subjects'] = csv_data['subjects']

                if csv_data.get('genres') and not metadata.get('genres'):
                    metadata['genres'] = csv_data['genres']

                updated_books += 1
                print(f"✓ Updated: {book['title']} by {book['author']} - {len(csv_data['isbns'])} ISBNs")

    print(f"\nMatches found: {matches_found}")
    print(f"Books updated: {updated_books}")

    # Write updated JSON back
    if updated_books > 0:
        print(f"\nWriting updated data to {json_path}...")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(books_data, f, indent=2, ensure_ascii=False)
        print("✓ Done!")
    else:
        print("\nNo updates made.")


if __name__ == '__main__':
    main()
