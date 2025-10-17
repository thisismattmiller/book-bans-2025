#!/usr/bin/env python3
"""
Scrape NCES district data and combine with CSV data into a JSON file.
"""

import csv
import json
import re
import time
import urllib.request
from html.parser import HTMLParser


class NCESDistrictParser(HTMLParser):
    """Parse NCES district detail page."""

    def __init__(self):
        super().__init__()
        self.data = {}
        self.current_section = None
        self.current_tag = None
        self.current_attrs = []
        self.in_target = False
        self.capture_next = None
        self.temp_data = {}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return

        # District Name
        if 'District Name:' in data:
            self.capture_next = 'district_name'
        elif self.capture_next == 'district_name' and data not in ['District Name:', '(Schools in this District)']:
            self.data['District Name'] = data
            self.capture_next = None

        # NCES District ID
        elif 'NCES District ID:' in data:
            self.capture_next = 'nces_id'
        elif self.capture_next == 'nces_id':
            self.data['NCES District ID'] = data
            self.capture_next = None

        # State District ID
        elif 'State District ID:' in data:
            self.capture_next = 'state_id'
        elif self.capture_next == 'state_id':
            self.data['State District ID'] = data
            self.capture_next = None

        # Mailing Address
        elif 'Mailing Address:' in data:
            self.capture_next = 'mailing_address'
            self.temp_data['mailing_parts'] = []
        elif self.capture_next == 'mailing_address' and data != 'Mailing Address:':
            self.temp_data['mailing_parts'].append(data)
            if len(self.temp_data['mailing_parts']) >= 2:
                self.data['Mailing Address'] = ' '.join(self.temp_data['mailing_parts'])
                self.capture_next = None

        # Physical Address
        elif 'Physical Address:' in data:
            self.capture_next = 'physical_address'
            self.temp_data['physical_parts'] = []
        elif self.capture_next == 'physical_address' and 'Physical Address:' not in data and 'Map latest data' not in data:
            self.temp_data['physical_parts'].append(data)
            if len(self.temp_data['physical_parts']) >= 2:
                self.data['Physical Address'] = ' '.join(self.temp_data['physical_parts'])
                self.capture_next = None

        # Phone
        elif 'Phone:' in data:
            self.capture_next = 'phone'
        elif self.capture_next == 'phone':
            self.data['Phone'] = data
            self.capture_next = None

        # Type
        elif 'Type:' in data:
            self.capture_next = 'type'
        elif self.capture_next == 'type':
            self.data['Type'] = data
            self.capture_next = None

        # Status
        elif 'Status:' in data:
            self.capture_next = 'status'
        elif self.capture_next == 'status':
            self.data['Status'] = data
            self.capture_next = None

        # Total Schools
        elif 'Total Schools:' in data:
            self.capture_next = 'total_schools'
        elif self.capture_next == 'total_schools':
            self.data['Total Schools'] = data
            self.capture_next = None

        # Grade Span
        elif 'Grade Span:' in data:
            self.capture_next = 'grade_span'
        elif self.capture_next == 'grade_span':
            self.data['Grade Span'] = data
            self.capture_next = None

        # Website
        elif 'Website:' in data:
            self.capture_next = 'website'
        elif self.capture_next == 'website' and data != 'Website:':
            if data.startswith('http'):
                self.data['Website'] = data
                self.capture_next = None

        # County
        elif 'County:' in data and self.current_tag == 'th':
            self.capture_next = 'county'
        elif self.capture_next == 'county' and self.current_tag == 'td':
            self.data['County'] = data
            self.capture_next = None

        # County ID
        elif 'County ID:' in data:
            self.capture_next = 'county_id'
        elif self.capture_next == 'county_id' and self.current_tag == 'td':
            self.data['County ID'] = data
            self.capture_next = None

        # Locale
        elif 'Locale:' in data and self.current_tag == 'th':
            self.capture_next = 'locale'
        elif self.capture_next == 'locale' and self.current_tag == 'td':
            self.data['Locale'] = data
            self.capture_next = None

        # Total Students
        elif 'Total Students:' in data:
            self.capture_next = 'total_students'
        elif self.capture_next == 'total_students' and self.current_tag == 'td':
            self.data['Total Students'] = data
            self.capture_next = None

        # Student/Teacher Ratio
        elif 'Student/Teacher Ratio:' in data:
            self.capture_next = 'student_teacher_ratio'
        elif self.capture_next == 'student_teacher_ratio' and self.current_tag == 'td':
            self.data['Student/Teacher Ratio'] = data
            self.capture_next = None

        # Total Revenue
        elif 'Total Revenue:' in data:
            self.capture_next = 'total_revenue'
        elif self.capture_next == 'total_revenue' and self.current_tag == 'font' and '$' in data:
            self.data['Total Revenue'] = data
            self.capture_next = None

        # Total Expenditures
        elif 'Total Expenditures:' in data:
            self.capture_next = 'total_expenditures'
        elif self.capture_next == 'total_expenditures' and self.current_tag == 'font' and '$' in data:
            self.data['Total Expenditures'] = data
            self.capture_next = None


def scrape_nces_data(nces_id):
    """
    Scrape district data from NCES website.

    Args:
        nces_id: NCES district ID

    Returns:
        dict: Scraped district data
    """
    url = f"https://nces.ed.gov/ccd/districtsearch/district_detail.asp?ID2={nces_id}"

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'user: thisismattmiller - data scripts'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')

        parser = NCESDistrictParser()
        parser.feed(html)

        return parser.data

    except Exception as e:
        print(f"    Error scraping NCES data for {nces_id}: {e}")
        return {}


def main():
    input_file = 'data/school_districts_with_qids.csv'
    output_file = 'data/school_districts.json'

    districts_data = {}

    # Read CSV file
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        for i, row in enumerate(reader, start=1):
            district_name = row.get('District', '').strip()
            state = row.get('State', '').strip()
            qid = row.get('Qid', '').strip()
            nces = row.get('NCES', '').strip()

            if not district_name:
                continue

            print(f"[{i}] Processing: {district_name}, {state}")

            # Initialize district data with CSV values
            district_data = {
                'State': state,
                'District': district_name,
                'Qid': qid,
                'NCES': nces
            }

            # If NCES ID is available, scrape the data
            if nces:
                print(f"    Scraping NCES data for {nces}...")
                nces_data = scrape_nces_data(nces)

                if nces_data:
                    district_data['nces_data'] = nces_data
                    print(f"    Successfully scraped data")
                else:
                    print(f"    No data scraped")

                # Rate limit
                time.sleep(1)
            else:
                print(f"    No NCES ID available")

            # Use district name as key
            districts_data[district_name] = district_data

    # Write JSON file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(districts_data, outfile, indent=2, ensure_ascii=False)

    print(f"\nProcessed {len(districts_data)} districts")
    print(f"Output written to {output_file}")


if __name__ == '__main__':
    main()
