#!/usr/bin/env python3
import json

with open('data/books_by_title.json', 'r') as f:
    books = json.load(f)

for book_id, book_data in books.items():
    metadata = book_data.get('metadata', {})
    oclc_numbers = metadata.get('oclc_numbers', [])

    if not oclc_numbers or len(oclc_numbers) == 0:
        title = metadata.get('title', 'N/A')
        author = metadata.get('author', 'N/A')
        print(f"{title} by {author}")
