#!/usr/bin/env python3
"""
Add county GeoJSON data to school districts based on County ID.
Matches NCES County ID to county GeoJSON GEOID10 field.
"""

import json


def main():
    # File paths
    county_geojson_file = '/Users/m/Downloads/county.geo.json'
    school_districts_file = 'data/school_districts.json'
    output_file = 'data/school_districts.json'

    # Load county GeoJSON
    print("Loading county GeoJSON data...")
    try:
        with open(county_geojson_file, 'r', encoding='utf-8') as f:
            county_data = json.load(f)
    except UnicodeDecodeError:
        print("UTF-8 encoding failed, trying latin-1...")
        with open(county_geojson_file, 'r', encoding='latin-1') as f:
            county_data = json.load(f)

    # Create a lookup dictionary: GEOID10 -> feature
    county_lookup = {}
    for feature in county_data.get('features', []):
        geoid = feature.get('properties', {}).get('GEOID10')
        if geoid:
            county_lookup[geoid] = feature

    print(f"Loaded {len(county_lookup)} county features")

    # Load school districts data
    print("Loading school districts data...")
    with open(school_districts_file, 'r', encoding='utf-8') as f:
        districts = json.load(f)

    # Match and add county GeoJSON to districts
    matched_count = 0
    no_nces_count = 0
    no_county_id_count = 0
    not_found_count = 0

    for district_name, district_data in districts.items():
        nces_data = district_data.get('nces_data', {})

        if not nces_data:
            no_nces_count += 1
            continue

        county_id = nces_data.get('County ID', '').strip()

        if not county_id:
            no_county_id_count += 1
            continue

        # Try to match with county GeoJSON
        if county_id in county_lookup:
            district_data['county_geojson'] = county_lookup[county_id]
            matched_count += 1
            print(f"Matched: {district_name} -> County ID {county_id}")
        else:
            not_found_count += 1
            print(f"No match: {district_name} -> County ID {county_id} not found in GeoJSON")

    # Write updated data back to file
    print(f"\nWriting updated data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(districts, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n=== Summary ===")
    print(f"Total districts: {len(districts)}")
    print(f"Successfully matched: {matched_count}")
    print(f"No NCES data: {no_nces_count}")
    print(f"No County ID: {no_county_id_count}")
    print(f"County ID not found in GeoJSON: {not_found_count}")


if __name__ == '__main__':
    main()
