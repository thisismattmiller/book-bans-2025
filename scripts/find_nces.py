#!/usr/bin/env python3
"""
Search Wikidata for school districts and match them by state.
Adds a Qid column with the Wikidata ID if a match is found.
"""

import csv
import time
import urllib.parse
import urllib.request
import json


# State name normalization mapping
STATE_ABBREVIATIONS = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY'
}

# Reverse mapping
STATE_FULL_NAMES = {v: k for k, v in STATE_ABBREVIATIONS.items()}


def normalize_state(state_text):
    """
    Normalize state names to both full name and abbreviation for comparison.

    Returns:
        tuple: (full_name, abbreviation)
    """
    state_text = state_text.strip()

    if state_text in STATE_ABBREVIATIONS:
        return state_text, STATE_ABBREVIATIONS[state_text]
    elif state_text in STATE_FULL_NAMES:
        return STATE_FULL_NAMES[state_text], state_text
    else:
        # Return as-is if not in mapping
        return state_text, state_text


def state_matches(description, state):
    """
    Check if state name (full or abbreviated) appears in the description.

    Args:
        description: The description text from Wikidata
        state: The state name from the CSV

    Returns:
        bool: True if state is found in description
    """
    if not description:
        return False

    description_lower = description.lower()
    state_full, state_abbr = normalize_state(state)

    # Check for full state name or abbreviation
    return (state_full.lower() in description_lower or
            state_abbr.lower() in description_lower)


def search_wikidata(district_name):
    """
    Search Wikidata for a school district.

    Args:
        district_name: Name of the school district

    Returns:
        list: Search results from Wikidata
    """
    base_url = "https://www.wikidata.org/w/api.php"
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'limit': '10',
        'language': 'en',
        'uselang': 'en',
        'type': 'item',
        'search': district_name
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'user: thisismattmiller - data scripts'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('search', [])
    except Exception as e:
        print(f"Error searching for {district_name}: {e}")
        return []


def get_nces_id(qid):
    """
    Query Wikidata SPARQL endpoint to get NCES ID for a given QID.

    Args:
        qid: Wikidata QID (e.g., 'Q6524588')

    Returns:
        str: NCES ID if found, empty string otherwise
    """
    sparql_endpoint = "https://query.wikidata.org/sparql"

    query = f"""
    SELECT ?NCES
    WHERE
    {{
      wd:{qid} wdt:P2483 ?NCES.
    }}
    """

    params = {
        'query': query,
        'format': 'json'
    }

    url = f"{sparql_endpoint}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'user: thisismattmiller - data scripts'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            results = data.get('results', {}).get('bindings', [])

            if results:
                return results[0].get('NCES', {}).get('value', '')
            return ''
    except Exception as e:
        print(f"    Error getting NCES ID for {qid}: {e}")
        return ''


def find_qid_for_district(district_name, state):
    """
    Find the Wikidata QID for a school district by matching state in description.

    Args:
        district_name: Name of the school district
        state: State where the district is located

    Returns:
        str: Wikidata QID if found, empty string otherwise
    """
    results = search_wikidata(district_name)

    for result in results:
        description = result.get('description', '')
        if state_matches(description, state):
            return result.get('id', '')

    return ''


def main():
    input_file = 'data/school_districts.csv'
    output_file = 'data/school_districts_with_qids.csv'

    # Read input CSV
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = list(reader.fieldnames)

        # Add Qid and NCES columns if not present
        if 'Qid' not in fieldnames:
            fieldnames.append('Qid')
        if 'NCES' not in fieldnames:
            fieldnames.append('NCES')

        rows = []
        for i, row in enumerate(reader, start=1):
            district = row.get('District', '').strip()
            state = row.get('State', '').strip()

            if district and state:
                print(f"[{i}] Searching for: {district}, {state}")
                qid = find_qid_for_district(district, state)

                if qid:
                    print(f"    Found QID: {qid}")
                    row['Qid'] = qid

                    # Get NCES ID from Wikidata
                    nces = get_nces_id(qid)
                    if nces:
                        print(f"    Found NCES: {nces}")
                        row['NCES'] = nces
                    else:
                        print(f"    No NCES ID found")
                        row['NCES'] = ''

                    # Rate limit for SPARQL query
                    time.sleep(0.5)
                else:
                    print(f"    No match found")
                    row['Qid'] = ''
                    row['NCES'] = ''

                # Be respectful to Wikidata API - rate limit requests
                time.sleep(0.5)
            else:
                row['Qid'] = ''
                row['NCES'] = ''

            rows.append(row)

    # Write output CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nProcessed {len(rows)} districts")
    print(f"Output written to {output_file}")


if __name__ == '__main__':
    main()
