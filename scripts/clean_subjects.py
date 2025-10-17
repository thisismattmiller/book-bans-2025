#!/usr/bin/env python3
"""
Clean subject headings in books_by_title.json using Google Gemini API.
Removes non-English, format-based subjects, and consolidates duplicates.
"""

import json
import os
from pathlib import Path
from google import genai
from google.genai import types


def clean_subjects_with_gemini(subjects_list, client, model="gemini-flash-latest"):
    """
    Send subjects list to Gemini API for cleaning.

    Args:
        subjects_list: List of subject headings
        client: Google GenAI client
        model: Model name to use

    Returns:
        Cleaned list of subjects as JSON array
    """
    if not subjects_list:
        return []

    # Convert list to JSON string for the prompt
    subjects_json = json.dumps(subjects_list)

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=subjects_json),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=-1,
        ),
        response_mime_type="application/json",
        system_instruction=[
            types.Part.from_text(text="""You are given a list of book subject headings, the task to to remove any heading that is non-english and or not content based, for example AUDIOBOOK or LARGE PRINT are not valid content based subject headings.
Remove any audience modifiers from the headings like JUVENILE FICTION or YOUNG ADULT FICTION and when them remove consolidate the headings if any of them are the same without those modifiers

Return the JSON array of headings with only the good headings."""),
        ],
    )

    # Collect the full response
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if chunk.text:
            response_text += chunk.text

    # Parse the JSON response
    try:
        cleaned_subjects = json.loads(response_text)
        return cleaned_subjects if isinstance(cleaned_subjects, list) else []
    except json.JSONDecodeError as e:
        print(f"    Error parsing Gemini response: {e}")
        print(f"    Response was: {response_text[:200]}...")
        return subjects_list  # Return original if parsing fails


def main():
    """Process all books and clean their subjects."""
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        print("Please set it with: export GEMINI_API_KEY='your-api-key'")
        return

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    base_dir = Path('data')
    books_file = base_dir / 'books_by_title.json'
    output_file = base_dir / 'books_by_title.json'

    # Load books data
    print(f"Loading books from {books_file}...")
    with open(books_file, 'r', encoding='utf-8') as f:
        books = json.load(f)

    print(f"Found {len(books)} books to process\n")

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for book_id, book_data in books.items():
        title = book_data.get('title', 'Unknown')
        metadata = book_data.get('metadata', {})
        subjects = metadata.get('subjects', [])

        # Skip if already cleaned or no subjects
        if 'subjects_clean' in metadata:
            print(f"[{book_id}] {title}: Already cleaned, skipping")
            skipped_count += 1
            continue

        if not subjects:
            print(f"[{book_id}] {title}: No subjects, skipping")
            skipped_count += 1
            continue

        print(f"[{book_id}] {title}")
        print(f"  Original subjects: {len(subjects)}")

        try:
            # Clean subjects using Gemini
            cleaned_subjects = clean_subjects_with_gemini(subjects, client)

            # Add cleaned subjects to metadata
            metadata['subjects_clean'] = cleaned_subjects

            print(f"  Cleaned subjects: {len(cleaned_subjects)}")
            print(f"  ✓ Cleaned and saved")
            processed_count += 1

            # Save after each book to avoid losing progress
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(books, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"  ✗ Error processing: {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total books: {len(books)}")
    print(f"  Processed: {processed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Errors: {error_count}")
    print(f"  Output: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
