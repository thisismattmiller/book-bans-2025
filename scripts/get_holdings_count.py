#!/usr/bin/env python3
"""
OCLC Holdings Count Script
Tests the WorldCat holdings endpoint to get library holdings information.
"""

import json
import os
import requests
import time


# Global variables for authentication
headers = {}
auth_timestamp = None


def reauth(oclc_client_id, oclc_secret):
    """Authenticate with OCLC API."""
    global headers
    global auth_timestamp

    if auth_timestamp is not None:
        sec_left = time.time() - auth_timestamp
        sec_left = 1199 - 1 - int(sec_left)

        if sec_left > 60:
            return True

    print("[VERBOSE] Authenticating with OCLC...")
    response = requests.post(
        'https://oauth.oclc.org/token',
        data={"grant_type": "client_credentials", 'scope': ['wcapi']},
        auth=(oclc_client_id, oclc_secret),
    )

    print(f"[VERBOSE] Auth response: {response.text}")

    response_data = response.json()
    if "access_token" not in response_data:
        print("[ERROR] access token not found (BAD KEY/SECRET?)")
        return False

    token = response_data["access_token"]
    auth_timestamp = time.time()

    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    print("[VERBOSE] Authentication successful")

    return True


def get_holdings_count(oclc_number, oclc_client_id, oclc_secret):
    """Get holdings count for an OCLC number."""
    global headers

    # Check if we need to reauth
    reauth_okay = reauth(oclc_client_id, oclc_secret)

    if not reauth_okay:
        return None

    url = f'https://americas.discovery.api.oclc.org/worldcat/search/v2/bibs-summary-holdings'

    params = {
        'oclcNumber': oclc_number,
        'holdingsAllEditions': 'true'
    }

    print(f"  [VERBOSE] Querying holdings with URL: {url}")
    print(f"  [VERBOSE] Query params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"  [VERBOSE] Response status: {response.status_code}")

        data = response.json()

        # Check if we got valid results
        if data.get('numberOfRecords', 0) > 0 and 'briefRecords' in data:
            return data
        else:
            print(f"  [VERBOSE] No holdings data returned")
            return None

    except Exception as e:
        print(f"  [ERROR] Error querying WorldCat holdings: {e}")
        return None


def load_books():
    """Load books from JSON file."""
    with open('data/books_by_title.json', 'r') as f:
        return json.load(f)


def save_books(books):
    """Save books to JSON file."""
    with open('data/books_by_title.json', 'w') as f:
        json.dump(books, f, indent=2)


def main():
    """Main execution function."""
    # Get OCLC credentials from environment
    oclc_client_id = os.environ.get('OCLC_CLIENT_ID')
    oclc_secret = os.environ.get('OCLC_SECRET')

    if not oclc_client_id or not oclc_secret:
        print("[ERROR] OCLC_CLIENT_ID and OCLC_SECRET environment variables must be set")
        return

    print("="*80)
    print("OCLC Holdings Count Script")
    print("="*80)
    print()

    print("[VERBOSE] Loading books from data/books_by_title.json...")
    books = load_books()
    total_books = len(books)
    print(f"[VERBOSE] Loaded {total_books} books total")

    # Count books with OCLC numbers that need holdings data
    books_needing_holdings = 0
    for book_data in books.values():
        metadata = book_data.get('metadata', {})
        oclc_numbers = metadata.get('oclc_numbers', [])
        has_holdings = 'holdings' in metadata

        if oclc_numbers and not has_holdings:
            books_needing_holdings += 1

    print(f"[VERBOSE] Found {books_needing_holdings} books with OCLC numbers but no holdings data")
    print("\n" + "="*80 + "\n")

    processed_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for book_id, book_data in books.items():
        metadata = book_data.get('metadata', {})
        oclc_numbers = metadata.get('oclc_numbers', [])
        has_holdings = 'holdings' in metadata

        # Skip if no OCLC numbers or already has holdings
        if not oclc_numbers or has_holdings:
            continue

        title = metadata.get('title', 'N/A')
        author = metadata.get('author', 'N/A')

        processed_count += 1
        print(f"\n[{processed_count}/{books_needing_holdings}] Processing Book ID: {book_id}")
        print(f"  Title: {title}")
        print(f"  Author: {author}")
        print(f"  OCLC numbers available: {len(oclc_numbers)}")

        # Try each OCLC number until we get holdings data
        holdings_data = None
        for idx, oclc_num in enumerate(oclc_numbers):
            print(f"  [VERBOSE] Trying OCLC number {idx + 1}/{len(oclc_numbers)}: {oclc_num}")

            holdings_data = get_holdings_count(oclc_num, oclc_client_id, oclc_secret)

            if holdings_data:
                print(f"  [SUCCESS] Got holdings data for OCLC number: {oclc_num}")
                if 'briefRecords' in holdings_data and holdings_data['briefRecords']:
                    brief_record = holdings_data['briefRecords'][0]
                    if 'institutionHolding' in brief_record:
                        total_count = brief_record['institutionHolding'].get('totalHoldingCount', 'N/A')
                        total_editions = brief_record['institutionHolding'].get('totalEditions', 'N/A')
                        print(f"    - Total Holdings: {total_count}")
                        print(f"    - Total Editions: {total_editions}")
                break
            else:
                print(f"  [VERBOSE] No holdings data for OCLC number: {oclc_num}")

            # Small delay between requests
            time.sleep(0.5)

        if holdings_data:
            # Store holdings data in metadata
            metadata['holdings'] = holdings_data
            updated_count += 1

            # Save after each successful update
            print(f"  [VERBOSE] Saving to disk...")
            save_books(books)
            print(f"  [VERBOSE] Save complete")
        else:
            print(f"  [RESULT] No holdings data found for any OCLC number")
            failed_count += 1

        # Rate limiting
        print(f"  [VERBOSE] Waiting 1 second before next request...")
        time.sleep(1)
        print("\n" + "-"*80)

    print("\n" + "="*80)
    print("[COMPLETE] Holdings count script complete!")
    print(f"  Total books: {total_books}")
    print(f"  Books needing holdings: {books_needing_holdings}")
    print(f"  Processed: {processed_count}")
    print(f"  Successfully updated: {updated_count}")
    print(f"  Failed/No match: {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print("="*80)


if __name__ == "__main__":
    main()
