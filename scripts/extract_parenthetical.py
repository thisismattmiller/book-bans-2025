#!/usr/bin/env python3
"""
Remove parenthetical text from Title column and create a new title_parenthetical column.
Also strips whitespace from the title.
"""

import csv
import re
import sys


def extract_parenthetical(title):
    """
    Extract parenthetical text from title and return cleaned title and parenthetical text.

    Args:
        title: Original title string

    Returns:
        tuple: (cleaned_title, parenthetical_text)
    """
    if not title:
        return '', ''

    # Find all parenthetical expressions
    pattern = r'\s*\([^)]*\)\s*'
    parentheticals = re.findall(pattern, title)

    # Remove parentheticals and strip
    cleaned_title = re.sub(pattern, ' ', title)
    cleaned_title = ' '.join(cleaned_title.split()).strip()

    # Combine all parenthetical text, strip whitespace
    parenthetical_text = ''.join(parentheticals).strip()

    return cleaned_title, parenthetical_text


def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_parenthetical.py <input_csv> <output_csv>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Read input CSV
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames)

        # Add new column after Title
        title_index = fieldnames.index('Title')
        fieldnames.insert(title_index + 1, 'title_parenthetical')

        rows = []
        for row in reader:
            title = row.get('Title', '')
            cleaned_title, parenthetical = extract_parenthetical(title)

            row['Title'] = cleaned_title
            row['title_parenthetical'] = parenthetical
            rows.append(row)

    # Write output CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Processed {len(rows)} rows from {input_file} to {output_file}")


if __name__ == '__main__':
    main()
