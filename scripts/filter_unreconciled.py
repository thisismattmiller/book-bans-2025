#!/usr/bin/env python3
"""
Filter rows from refined_data_pass_one.csv that don't have any Mode Title values populated.
Creates a new file refined_data_pass_two.csv with unreconciled rows.
"""

import csv
import os


def main():
    # Define file paths
    input_file = os.path.join('data', 'refined_data_pass_one.csv')
    output_file = os.path.join('data', 'refined_data_pass_two.csv')

    # Read input CSV and filter rows
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        # Filter rows where Mode Title, Mode Title2, and Mode Title3 are all empty
        unreconciled_rows = []
        for row in reader:
            mode_title = row.get('Mode Title', '').strip()
            mode_title2 = row.get('Mode Title2', '').strip()
            mode_title3 = row.get('Mode Title3', '').strip()

            # If all three Mode Title fields are empty, include this row
            if not mode_title and not mode_title2 and not mode_title3:
                unreconciled_rows.append(row)

    # Write filtered rows to output CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unreconciled_rows)

    print(f"Filtered {len(unreconciled_rows)} unreconciled rows to {output_file}")


if __name__ == '__main__':
    main()
