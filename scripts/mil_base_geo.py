#!/usr/bin/env python3
"""
Fetch geolocation data for military bases using Google Places API.
"""

import os
import json
import requests
from typing import Dict, List, Optional


MILITARY_BASES = [
    "Marine Corps Base Camp Lejeune, NC",
    "Fort Bragg, NC",
    "Marine Corps Air Station New River, NC",
    "Naval Surface Warfare Center Dahlgren Division, VA",
    "Marine Corps Base Quantico, VA",
    "USMA West Point, NY",
    "Guantanamo Bay Naval Station, Cuba",
    "Coast Guard Air Station Borinquen, PR",
    "Fort Buchanan, PR",
    "Fort Benning, GA",
    "Fort Campbell, KY",
    "Fort Jackson, SC",
    "Fort Knox, KY",
    "Fort Rucker, AL",
    "Fort Stewart, GA",
    "Maxwell Air Force Base, AL",
    "Marine Corps Air Station Beaufort, SC",
]


def get_place_details(base_name: str, api_key: str) -> Optional[Dict]:
    """
    Fetch place details from Google Places API (New) for a given military base.

    Args:
        base_name: Name of the military base
        api_key: Google Places API key

    Returns:
        Dictionary containing place details or None if not found
    """
    # Use the new Places API (New) Text Search endpoint
    search_url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.types,places.plusCode"
    }

    body = {
        "textQuery": base_name
    }

    try:
        response = requests.post(search_url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        print(f"\nDEBUG - Response for '{base_name}':")
        print(f"  Full response: {json.dumps(data, indent=2)}")

        if "places" not in data or len(data["places"]) == 0:
            print(f"✗ No results found for: {base_name}")
            return None

        # Get the first result
        place = data["places"][0]

        result = {
            "name": base_name,
            "place_id": place.get("id"),
            "formatted_name": place.get("displayName", {}).get("text"),
            "formatted_address": place.get("formattedAddress"),
            "lat": place["location"]["latitude"],
            "lng": place["location"]["longitude"],
            "types": place.get("types", []),
        }

        if "plusCode" in place:
            result["plus_code"] = place["plusCode"]

        print(f"✓ Found: {base_name}")
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {base_name}: {e}")
        return None
    except (KeyError, TypeError) as e:
        print(f"Error parsing response for {base_name}: {e}")
        print(f"Response data: {json.dumps(data, indent=2)}")
        return None


def main():
    """Main function to fetch all military base locations."""
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    if not api_key:
        print("Error: GOOGLE_PLACES_API_KEY environment variable not set")
        print("Please set it with: export GOOGLE_PLACES_API_KEY='your-api-key'")
        return

    results = []

    print(f"Fetching geolocation data for {len(MILITARY_BASES)} military bases...\n")

    for base in MILITARY_BASES:
        place_data = get_place_details(base, api_key)
        if place_data:
            results.append(place_data)

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Write results to JSON file
    output_path = "data/mil_bases.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Successfully wrote {len(results)} military base locations to {output_path}")


if __name__ == "__main__":
    main()
