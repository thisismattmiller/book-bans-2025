#!/usr/bin/env python3
"""
Enrich refined_data_pass_one.csv with Mode Title data from refined_data_pass_two_enriched.csv.
For rows missing Mode Title, Mode Title2, or Mode Title3, look up the data from pass two.
"""

import csv
from pathlib import Path


def read_csv_as_dict(file_path):
    """Read CSV file and return list of dictionaries."""
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def normalize_title(title):
    """Normalize title for comparison."""
    return title.strip().lower()


def build_pass_two_lookup(pass_two_data):
    """Build a lookup dictionary from pass two data using combined title + parenthetical."""
    lookup = {}

    for row in pass_two_data:
        title = row.get('Title', '').strip()
        parenthetical = row.get('title_parenthetical', '').strip()

        # Create combined title
        if parenthetical:
            combined_title = f"{title} {parenthetical}"
        else:
            combined_title = title

        # Normalize for lookup
        key = normalize_title(combined_title)
        lookup[key] = row

    return lookup


def is_empty(value):
    """Check if a value is empty or just whitespace."""
    return not value or not value.strip()


def main():
    """Enrich pass one data with Mode Title values from pass two."""
    base_dir = Path('data')
    pass_one_file = base_dir / 'refined_data_pass_one.csv'
    pass_two_file = base_dir / 'refined_data_pass_two_enriched.csv'
    output_file = base_dir / 'refined_data_all.csv'

    # Read both files
    print("Reading pass one data...")
    pass_one_data, pass_one_fields = read_csv_as_dict(pass_one_file)

    print("Reading pass two enriched data...")
    pass_two_data, pass_two_fields = read_csv_as_dict(pass_two_file)

    # Build lookup from pass two
    print("Building lookup index from pass two data...")
    pass_two_lookup = build_pass_two_lookup(pass_two_data)
    print(f"  Created lookup with {len(pass_two_lookup)} entries")

    # Process pass one data
    enriched_count = 0
    not_found_count = 0

    print("\nProcessing pass one data...")
    for row in pass_one_data:
        title = row.get('Title', '').strip()

        # Check if Mode Title columns are empty
        mode_title = row.get('Mode Title', '')
        mode_title2 = row.get('Mode Title2', '')
        mode_title3 = row.get('Mode Title3', '')

        if is_empty(mode_title) and is_empty(mode_title2) and is_empty(mode_title3):
            # Look up in pass two data
            key = normalize_title(title)

            if key in pass_two_lookup:
                pass_two_row = pass_two_lookup[key]

                # Copy Mode Title values from pass two
                if 'Mode Title' in pass_two_fields and pass_two_row.get('Mode Title'):
                    row['Mode Title'] = pass_two_row['Mode Title']
                if 'Mode Title2' in pass_two_fields and pass_two_row.get('Mode Title2'):
                    row['Mode Title2'] = pass_two_row['Mode Title2']
                if 'Mode Title3' in pass_two_fields and pass_two_row.get('Mode Title3'):
                    row['Mode Title3'] = pass_two_row['Mode Title3']

                enriched_count += 1
                print(f"  ✓ Enriched: {title}")
            else:
                not_found_count += 1
                print(f"  ✗ Not found: {title}")

    # Write enriched data
    print(f"\nWriting enriched data to {output_file}...")
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=pass_one_fields)
        writer.writeheader()
        writer.writerows(pass_one_data)

    print(f"\n✓ Successfully enriched data:")
    print(f"  - Total rows in pass one: {len(pass_one_data)}")
    print(f"  - Rows enriched with Mode Title data: {enriched_count}")
    print(f"  - Rows not found in pass two: {not_found_count}")
    print(f"  - Output file: {output_file}")


if __name__ == "__main__":
    main()
