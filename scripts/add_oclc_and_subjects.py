#!/usr/bin/env python3
"""
OCLC and Subjects Addition Script
Searches WorldCat by ISBN for books without OCLC numbers and populates metadata.
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


def _get_creator_name(contributor_info):
    """
    Finds and formats the name of a suitable creator (author).
    Returns formatted name as "Last, First" if possible.
    """
    if not isinstance(contributor_info, dict):
        return None
    creators = contributor_info.get('creators')
    if not isinstance(creators, list):
        return None

    # Roles that disqualify a person from being a "creator only"
    non_creator_roles = {
        'editor', 'compiler', 'voice actor', 'ed.lit', 'mitwirkender',
        'buchgestalter', 'herausgeber', 'drucker', 'buchbinder', 'issuing body',
        'hörfunkproduzent', 'verlag', 'regisseur', 'synchronsprecher', 'narrator'
    }

    for creator in creators:
        if not isinstance(creator, dict) or creator.get('type') != 'person':
            continue

        is_creator_only = True
        relators = creator.get('relators')
        if isinstance(relators, list):
            for relator in relators:
                term = (relator or {}).get('term', '').lower()
                if term in non_creator_roles:
                    is_creator_only = False
                    break

        if is_creator_only:
            first_name_val = creator.get('firstName')
            second_name_val = creator.get('secondName')

            first_name, second_name = None, None

            if isinstance(first_name_val, dict):
                first_name = first_name_val.get('text')
            elif isinstance(first_name_val, str):
                first_name = first_name_val

            if isinstance(second_name_val, dict):
                second_name = second_name_val.get('text')
            elif isinstance(second_name_val, str):
                second_name = second_name_val

            if second_name and first_name:
                return f"{second_name}, {first_name}"
            elif second_name:
                return second_name
            elif first_name:
                return first_name

    return None


def _extract_bib_data(data):
    """
    Extracts and simplifies bibliographic data from WorldCat response.
    """
    if not isinstance(data, dict) or not isinstance(data.get('bibRecords'), list):
        return []

    simplified_records = []

    for record in data['bibRecords']:
        if not isinstance(record, dict):
            continue

        identifier = record.get('identifier') or {}
        title_info = record.get('title') or {}
        contributor_info = record.get('contributor') or {}
        date_info = record.get('date') or {}
        language_info = record.get('language') or {}
        format_info = record.get('format') or {}
        work_info = record.get('work') or {}

        # Extract main title
        main_titles = title_info.get('mainTitles')
        main_title_text = None
        if isinstance(main_titles, list) and main_titles:
            first_title = main_titles[0]
            if isinstance(first_title, dict):
                main_title_text = first_title.get('text')

        # Extract statement of responsibility
        sor = contributor_info.get('statementOfResponsibility')
        sor_text = (sor or {}).get('text')

        # Extract subjects
        subjects_list = record.get('subjects')
        subjects_str_list = None
        if isinstance(subjects_list, list):
            subjects_str_list = []
            for s in subjects_list:
                subject_name = (s or {}).get('subjectName')
                if isinstance(subject_name, dict):
                    text = subject_name.get('text')
                    if text:
                        subjects_str_list.append(text)

        simplified_record = {
            'oclcNumber': identifier.get('oclcNumber'),
            'isbns': identifier.get('isbns'),
            'mergedOclcNumbers': identifier.get('mergedOclcNumbers'),
            'lccn': identifier.get('lccn'),
            'creator': _get_creator_name(contributor_info),
            'mainTitle': main_title_text,
            'statementOfResponsibility': sor_text,
            'classifications': record.get('classification'),
            'subjects': subjects_str_list,
            'publicationDate': date_info.get('publicationDate'),
            'itemLanguage': language_info.get('itemLanguage'),
            'generalFormat': format_info.get('generalFormat'),
            'workId': work_info.get('id')
        }

        simplified_records.append(simplified_record)

    return simplified_records


def search_worldcat_by_isbn(isbn, oclc_client_id, oclc_secret):
    """Search WorldCat by ISBN."""
    global headers

    # Check if we need to reauth
    reauth_okay = reauth(oclc_client_id, oclc_secret)

    if not reauth_okay:
        return None

    url = 'https://americas.discovery.api.oclc.org/worldcat/search/v2/bibs'

    params = {
        'q': f'bn:{isbn}',
        'limit': 10
    }

    print(f"  [VERBOSE] Searching WorldCat with URL: {url}")
    print(f"  [VERBOSE] Query params: {params}")

    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"  [VERBOSE] Response status: {response.status_code}")

        data = response.json()
        print(f"  [VERBOSE] Number of records found: {data.get('numberOfRecords', 0)}")

        if data.get('numberOfRecords', 0) == 0:
            return None

        # Extract and return the bibliographic data
        extracted_data = _extract_bib_data(data)
        return extracted_data[0] if extracted_data else None

    except Exception as e:
        print(f"  [ERROR] Error querying WorldCat: {e}")
        return None


def load_books():
    """Load books from JSON file."""
    with open('data/books_by_title.json', 'r') as f:
        return json.load(f)


def save_books(books):
    """Save books to JSON file."""
    with open('data/books_by_title.json', 'w') as f:
        json.dump(books, f, indent=2)


def update_book_with_worldcat_data(book_data, worldcat_record):
    """Update book metadata with WorldCat data."""
    print(f"  [VERBOSE] Updating book metadata from WorldCat...")

    metadata = book_data['metadata']

    # Update OCLC number
    if worldcat_record.get('oclcNumber'):
        if 'oclc_numbers' not in metadata:
            metadata['oclc_numbers'] = []

        oclc_num = worldcat_record['oclcNumber']
        if oclc_num not in metadata['oclc_numbers']:
            metadata['oclc_numbers'].append(oclc_num)
            print(f"  [VERBOSE] Added OCLC number: {oclc_num}")

        # Add merged OCLC numbers if available
        if worldcat_record.get('mergedOclcNumbers'):
            for merged_num in worldcat_record['mergedOclcNumbers']:
                if merged_num not in metadata['oclc_numbers']:
                    metadata['oclc_numbers'].append(merged_num)
            print(f"  [VERBOSE] Added {len(worldcat_record['mergedOclcNumbers'])} merged OCLC numbers")

    # Update subjects
    if worldcat_record.get('subjects'):
        # Ensure subjects is a list
        if 'subjects' not in metadata:
            metadata['subjects'] = []
        elif not isinstance(metadata['subjects'], list):
            # Convert to list if it's a string or other type
            metadata['subjects'] = [metadata['subjects']] if metadata['subjects'] else []

        for subject in worldcat_record['subjects']:
            if subject not in metadata['subjects']:
                metadata['subjects'].append(subject)

        print(f"  [VERBOSE] Added/updated subjects ({len(worldcat_record['subjects'])} total)")

    # Update LCCN if missing
    if worldcat_record.get('lccn') and not metadata.get('lccn'):
        if 'lccn' not in metadata:
            metadata['lccn'] = []
        if isinstance(metadata['lccn'], list):
            if worldcat_record['lccn'] not in metadata['lccn']:
                metadata['lccn'].append(worldcat_record['lccn'])
        print(f"  [VERBOSE] Added LCCN: {worldcat_record['lccn']}")

    # Update classifications
    if worldcat_record.get('classifications'):
        metadata['classifications'] = worldcat_record['classifications']
        print(f"  [VERBOSE] Added classifications")

    # Update publication date if missing
    if worldcat_record.get('publicationDate') and not metadata.get('publishedDate'):
        metadata['publishedDate'] = worldcat_record['publicationDate']
        print(f"  [VERBOSE] Added publication date: {worldcat_record['publicationDate']}")

    # Update language if missing
    if worldcat_record.get('itemLanguage') and not metadata.get('language'):
        metadata['language'] = worldcat_record['itemLanguage']
        print(f"  [VERBOSE] Added language: {worldcat_record['itemLanguage']}")

    # Update format if missing
    if worldcat_record.get('generalFormat') and not metadata.get('generalFormat'):
        metadata['generalFormat'] = worldcat_record['generalFormat']
        print(f"  [VERBOSE] Added format: {worldcat_record['generalFormat']}")

    # Store the complete WorldCat record for reference
    metadata['worldcat_record'] = worldcat_record
    print(f"  [VERBOSE] Stored complete WorldCat record")

    return book_data


def main():
    """Main execution function."""
    # Get OCLC credentials from environment
    oclc_client_id = os.environ.get('OCLC_CLIENT_ID')
    oclc_secret = os.environ.get('OCLC_SECRET')

    if not oclc_client_id or not oclc_secret:
        print("[ERROR] OCLC_CLIENT_ID and OCLC_SECRET environment variables must be set")
        return

    print("[VERBOSE] Starting OCLC and Subjects addition script...")
    print("[VERBOSE] Loading books from data/books_by_title.json...")

    books = load_books()
    total_books = len(books)
    print(f"[VERBOSE] Loaded {total_books} books total")

    # Count books needing OCLC numbers
    books_needing_oclc = 0
    for book_data in books.values():
        metadata = book_data.get('metadata', {})
        oclc_numbers = metadata.get('oclc_numbers', [])
        isbns = metadata.get('isbns', [])

        if (not oclc_numbers or len(oclc_numbers) == 0) and (isbns and len(isbns) > 0):
            books_needing_oclc += 1

    print(f"[VERBOSE] Found {books_needing_oclc} books with ISBNs but no OCLC numbers")
    print("\n" + "="*80 + "\n")

    processed_count = 0
    updated_count = 0
    skipped_count = 0
    failed_count = 0

    for book_id, book_data in books.items():
        metadata = book_data.get('metadata', {})
        oclc_numbers = metadata.get('oclc_numbers', [])
        isbns = metadata.get('isbns', [])

        # Skip if already has OCLC number or no ISBNs
        if (oclc_numbers and len(oclc_numbers) > 0) or (not isbns or len(isbns) == 0):
            continue

        title = metadata.get('title', 'N/A')
        author = metadata.get('author', 'N/A')

        processed_count += 1
        print(f"\n[{processed_count}/{books_needing_oclc}] Processing Book ID: {book_id}")
        print(f"  Title: {title}")
        print(f"  Author: {author}")
        print(f"  ISBNs available: {len(isbns)}")

        # Try each ISBN until we get a hit
        worldcat_record = None
        for idx, isbn in enumerate(isbns):
            print(f"  [VERBOSE] Trying ISBN {idx + 1}/{len(isbns)}: {isbn}")

            worldcat_record = search_worldcat_by_isbn(isbn, oclc_client_id, oclc_secret)

            if worldcat_record:
                print(f"  [SUCCESS] Found match with ISBN: {isbn}")
                print(f"    - WorldCat Title: {worldcat_record.get('mainTitle', 'N/A')}")
                print(f"    - WorldCat Author: {worldcat_record.get('creator', 'N/A')}")
                print(f"    - OCLC Number: {worldcat_record.get('oclcNumber', 'N/A')}")
                break
            else:
                print(f"  [VERBOSE] No match for ISBN: {isbn}")

            # Small delay between ISBN searches
            time.sleep(0.5)

        if worldcat_record:
            # Update the book with WorldCat data
            book_data = update_book_with_worldcat_data(book_data, worldcat_record)
            books[book_id] = book_data
            updated_count += 1

            # Save after each successful update
            print(f"  [VERBOSE] Saving to disk...")
            save_books(books)
            print(f"  [VERBOSE] Save complete")
        else:
            print(f"  [RESULT] No WorldCat match found for any ISBN")
            failed_count += 1

        # Rate limiting
        print(f"  [VERBOSE] Waiting 1 second before next request...")
        time.sleep(1)
        print("\n" + "-"*80)

    print("\n" + "="*80)
    print("[COMPLETE] OCLC and Subjects addition complete!")
    print(f"  Total books: {total_books}")
    print(f"  Books needing OCLC: {books_needing_oclc}")
    print(f"  Processed: {processed_count}")
    print(f"  Successfully updated: {updated_count}")
    print(f"  Failed/No match: {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print("="*80)


if __name__ == "__main__":
    main()
