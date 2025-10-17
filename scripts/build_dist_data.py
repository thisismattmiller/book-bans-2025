#!/usr/bin/env python3
"""
Build Distribution Data Script
Takes the full books_by_title.json and creates a minimal array for the interface.
"""

import json
import os


def load_books():
    """Load books from JSON file."""
    with open('data/books_by_title.json', 'r') as f:
        return json.load(f)


def clean_subjects(subjects):
    """Clean subjects by removing '--Fiction' suffix."""
    if not subjects:
        return subjects

    if isinstance(subjects, list):
        return [s.replace('--Fiction', '') for s in subjects]
    elif isinstance(subjects, str):
        return subjects.replace('--Fiction', '')

    return subjects


def calculate_popularity_stats(books):
    """Calculate statistics for holdings and editions to determine popularity tiers."""
    holdings_counts = []
    editions_counts = []

    for book_id, book_data in books.items():
        metadata = book_data.get('metadata', {})
        holdings_data = metadata.get('holdings', {})

        if holdings_data and 'briefRecords' in holdings_data:
            brief_records = holdings_data.get('briefRecords', [])
            if brief_records:
                first_record = brief_records[0]
                institution_holding = first_record.get('institutionHolding', {})

                total_holding_count = institution_holding.get('totalHoldingCount')
                total_editions = institution_holding.get('totalEditions')

                if total_holding_count is not None:
                    holdings_counts.append(total_holding_count)
                if total_editions is not None:
                    editions_counts.append(total_editions)

    if not holdings_counts:
        return None

    holdings_counts.sort()
    editions_counts.sort()

    # Calculate quartiles for holdings
    holdings_avg = sum(holdings_counts) / len(holdings_counts)
    holdings_q1 = holdings_counts[len(holdings_counts) // 4]
    holdings_q2 = holdings_counts[len(holdings_counts) // 2]
    holdings_q3 = holdings_counts[3 * len(holdings_counts) // 4]

    # Calculate quartiles for editions if we have data
    editions_avg = sum(editions_counts) / len(editions_counts) if editions_counts else 0
    editions_q2 = editions_counts[len(editions_counts) // 2] if editions_counts else 0

    return {
        'holdings_avg': holdings_avg,
        'holdings_q1': holdings_q1,
        'holdings_q2': holdings_q2,
        'holdings_q3': holdings_q3,
        'editions_avg': editions_avg,
        'editions_q2': editions_q2
    }


def determine_popularity(total_holding_count, total_editions, stats):
    """Determine popularity level based on holdings and editions."""
    if not stats or total_holding_count is None:
        return None

    # Create a composite score based on holdings (weighted more) and editions
    holdings_score = total_holding_count
    editions_score = (total_editions or 0) * 50  # Weight editions to be comparable to holdings

    composite_score = holdings_score + editions_score

    # Calculate thresholds based on quartiles
    threshold_very_popular = stats['holdings_q3'] + (stats['editions_q2'] * 50)
    threshold_popular = stats['holdings_q2'] + (stats['editions_q2'] * 50)
    threshold_medium = stats['holdings_q1'] + (stats['editions_q2'] * 25)

    if composite_score >= threshold_very_popular:
        return 'Very Popular'
    elif composite_score >= threshold_popular:
        return 'Popular'
    elif composite_score >= threshold_medium:
        return 'Medium'
    else:
        return 'Less Popular'


def build_minimal_data(books, stats):
    """Build minimal data array for the interface."""
    minimal_books = []

    for book_id, book_data in books.items():
        metadata = book_data.get('metadata', {})
        bans = book_data.get('bans', [])

        # Extract first values from arrays or None
        isbns = metadata.get('isbns', [])
        first_isbn = isbns[0] if isbns else None

        oclc_numbers = metadata.get('oclc_numbers', [])
        first_oclc = oclc_numbers[0] if oclc_numbers else None

        lccn = metadata.get('lccn', [])
        first_lccn = lccn[0] if lccn else None

        page_counts = metadata.get('page_counts', [])
        first_page_count = page_counts[0] if page_counts else None

        # Clean subjects
        subjects = clean_subjects(metadata.get('subjects_clean'))

        # Extract holdings data
        holdings_data = metadata.get('holdings', {})
        total_holding_count = None
        total_editions = None

        if holdings_data and 'briefRecords' in holdings_data:
            brief_records = holdings_data.get('briefRecords', [])
            if brief_records:
                first_record = brief_records[0]
                institution_holding = first_record.get('institutionHolding', {})
                total_holding_count = institution_holding.get('totalHoldingCount')
                total_editions = institution_holding.get('totalEditions')

        # Determine popularity level
        popularity_level = determine_popularity(total_holding_count, total_editions, stats)

        # Build minimal record
        minimal_record = {
            'id': book_id,
            'title': metadata.get('title'),
            'author': metadata.get('author'),
            'isbn': first_isbn,
            'oclc': first_oclc,
            'lccn': first_lccn,
            'description': metadata.get('description'),
            'pageCount': first_page_count,
            'subjects': subjects,
            'bans': bans,
            'totalHoldingCount': total_holding_count,
            'totalEditions': total_editions,
            'popularityLevel': popularity_level
        }

        minimal_books.append(minimal_record)

    return minimal_books


def save_dist_data(minimal_books):
    """Save minimal data to apps/public/data.json."""
    # Ensure the directory exists
    os.makedirs('apps/public', exist_ok=True)

    with open('apps/public/data.json', 'w') as f:
        json.dump(minimal_books, f, indent=2)


def main():
    """Main execution function."""
    print("="*80)
    print("Build Distribution Data Script")
    print("="*80)
    print()

    print("[VERBOSE] Loading books from data/books_by_title.json...")
    books = load_books()
    print(f"[VERBOSE] Loaded {len(books)} books")

    print("[VERBOSE] Calculating popularity statistics...")
    stats = calculate_popularity_stats(books)
    if stats:
        print(f"[VERBOSE] Holdings average: {stats['holdings_avg']:.2f}")
        print(f"[VERBOSE] Holdings Q1/Q2/Q3: {stats['holdings_q1']}/{stats['holdings_q2']}/{stats['holdings_q3']}")
        print(f"[VERBOSE] Editions average: {stats['editions_avg']:.2f}")
    else:
        print("[VERBOSE] No holdings data found, popularity levels will be None")

    print("[VERBOSE] Building minimal data array...")
    minimal_books = build_minimal_data(books, stats)
    print(f"[VERBOSE] Created {len(minimal_books)} minimal book records")

    # Count popularity levels
    if stats:
        popularity_counts = {}
        for book in minimal_books:
            level = book.get('popularityLevel')
            popularity_counts[level] = popularity_counts.get(level, 0) + 1
        print("[VERBOSE] Popularity distribution:")
        for level, count in sorted(popularity_counts.items(), key=lambda x: (x[0] is None, x[0])):
            print(f"  {level}: {count}")

    print("[VERBOSE] Saving to apps/public/data.json...")
    save_dist_data(minimal_books)
    print(f"[VERBOSE] Saved successfully")

    print()
    print("="*80)
    print("[COMPLETE] Distribution data built successfully!")
    print(f"  Output: apps/public/data.json")
    print(f"  Records: {len(minimal_books)}")
    print("="*80)


if __name__ == "__main__":
    main()
