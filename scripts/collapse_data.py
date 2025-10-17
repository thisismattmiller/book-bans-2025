#!/usr/bin/env python3
"""
Collapse refined_data_all.csv into two JSON files:
1. books_by_title.json - titles with array of (State, District, Date, Ban Status)
2. books_by_district.json - (State, District) with array of banned titles
"""

import csv
import json
from pathlib import Path
from collections import defaultdict


def merge_pipe_separated_values(*values):
    """Merge multiple pipe-separated values, removing duplicates."""
    all_items = []
    for value in values:
        if value and value.strip():
            items = [item.strip() for item in value.split('|')]
            all_items.extend(items)

    # Remove duplicates while preserving order
    seen = set()
    unique_items = []
    for item in all_items:
        if item and item not in seen:
            seen.add(item)
            unique_items.append(item)

    return unique_items


def merge_fields(row):
    """Merge related fields from different sources into consolidated fields."""
    merged = {}

    # Title - use the main Title field
    merged['title'] = row.get('Title', '').strip()

    # Author
    merged['author'] = row.get('Author', '').strip()
    merged['secondary_authors'] = row.get('Secondary Author(s)', '').strip()
    merged['illustrators'] = row.get('Illustrator(s)', '').strip()
    merged['translators'] = row.get('Translator(s)', '').strip()

    # Series
    merged['series'] = row.get('Series', '').strip()

    # Format
    merged['formats'] = merge_pipe_separated_values(row.get('Format', ''))

    # ISBN - merge ISBN, ISBN2, ISBN Cluster
    merged['isbns'] = merge_pipe_separated_values(
        row.get('ISBN', ''),
        row.get('ISBN2', ''),
        row.get('ISBN Cluster', '')
    )

    # OCLC Numbers
    merged['oclc_numbers'] = merge_pipe_separated_values(
        row.get('OCLC Number', ''),
        row.get('OCLC', '')
    )

    # LCCN
    merged['lccn'] = merge_pipe_separated_values(
        row.get('LCCN', ''),
        row.get('LCCN2', '')
    )

    # Library of Congress Classification
    merged['lc_classification'] = merge_pipe_separated_values(
        row.get('Library of Congress Classification', '')
    )

    # Dewey Decimal
    merged['dewey_decimal'] = merge_pipe_separated_values(
        row.get('Dewey Decimal Classification', '')
    )

    # Mode Title - merge Mode Title, Mode Title2, Mode Title3
    mode_titles = merge_pipe_separated_values(
        row.get('Mode Title', ''),
        row.get('Mode Title2', ''),
        row.get('Mode Title3', '')
    )
    merged['mode_titles'] = mode_titles

    # Title variations
    merged['title_oclc'] = row.get('oclc_title', '').strip()
    merged['title_google'] = row.get('title_google', '').strip()
    merged['title_lc'] = row.get('title_LC', '').strip()

    # Subjects - merge Subjects and Subject Headings
    merged['subjects'] = merge_pipe_separated_values(
        row.get('Subjects', ''),
        row.get('Subject Headings', '')
    )

    # Genres
    merged['genres'] = merge_pipe_separated_values(row.get('Genres', ''))

    # Work URI
    merged['work_uris'] = merge_pipe_separated_values(row.get('Work URI', ''))

    # Description
    merged['description'] = row.get('Description', '').strip()

    # Page Count
    merged['page_counts'] = merge_pipe_separated_values(row.get('Page Count', ''))

    return merged


def main():
    """Process the CSV and create JSON outputs."""
    base_dir = Path('data')
    input_file = base_dir / 'refined_data_all.csv'
    output_by_title = base_dir / 'books_by_title.json'
    output_by_district = base_dir / 'books_by_district.json'

    print(f"Reading {input_file}...")

    # Data structures
    books_by_title = defaultdict(lambda: {
        'metadata': None,
        'bans': []
    })
    books_by_district = defaultdict(list)
    title_to_id = {}  # Map titles to IDs
    next_id = 1

    # Read CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            title = row.get('Title', '').strip()
            state = row.get('State', '').strip()
            district = row.get('District', '').strip()
            date = row.get('Date of Challenge/Removal', '').strip()
            ban_status = row.get('Ban Status', '').strip()

            if not title:
                continue

            # Assign ID to title if not already assigned
            if title not in title_to_id:
                title_to_id[title] = next_id
                next_id += 1

            book_id = title_to_id[title]

            # Merge fields for this row
            merged_metadata = merge_fields(row)

            # Update books_by_title
            if books_by_title[title]['metadata'] is None:
                books_by_title[title]['metadata'] = merged_metadata
            else:
                # Merge arrays from multiple rows of the same title
                existing = books_by_title[title]['metadata']

                # Merge list fields
                for field in ['formats', 'isbns', 'oclc_numbers', 'lccn', 'lc_classification',
                              'dewey_decimal', 'mode_titles', 'subjects', 'genres',
                              'work_uris', 'page_counts']:
                    if field in merged_metadata:
                        combined = existing[field] + merged_metadata[field]
                        # Remove duplicates
                        seen = set()
                        unique = []
                        for item in combined:
                            if item not in seen:
                                seen.add(item)
                                unique.append(item)
                        existing[field] = unique

                # Keep longer description if available
                if merged_metadata.get('description') and \
                   len(merged_metadata['description']) > len(existing.get('description', '')):
                    existing['description'] = merged_metadata['description']

            # Add ban information
            ban_info = {
                'state': state,
                'district': district,
                'date': date,
                'ban_status': ban_status
            }
            books_by_title[title]['bans'].append(ban_info)

            # Update books_by_district
            district_key = f"{state} - {district}"
            book_entry = {
                'id': book_id,
                'title': title,
                'author': merged_metadata.get('author', ''),
                'date': date,
                'ban_status': ban_status
            }
            books_by_district[district_key].append(book_entry)

    # Convert defaultdicts to regular dicts for JSON serialization with IDs
    books_by_title_output = {
        title_to_id[title]: {
            'id': title_to_id[title],
            'title': title,
            'metadata': data['metadata'],
            'bans': data['bans']
        }
        for title, data in books_by_title.items()
    }

    books_by_district_output = dict(books_by_district)

    # Write JSON files
    print(f"\nWriting {output_by_title}...")
    with open(output_by_title, 'w', encoding='utf-8') as f:
        json.dump(books_by_title_output, f, indent=2, ensure_ascii=False)

    print(f"Writing {output_by_district}...")
    with open(output_by_district, 'w', encoding='utf-8') as f:
        json.dump(books_by_district_output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Successfully created JSON files:")
    print(f"  - Unique titles: {len(books_by_title_output)}")
    print(f"  - Unique districts: {len(books_by_district_output)}")
    print(f"  - Output files:")
    print(f"    • {output_by_title}")
    print(f"    • {output_by_district}")


if __name__ == "__main__":
    main()
