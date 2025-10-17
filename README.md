# Book Bans 2025


Read the blog post here: https://thisismattmiller.com/post/book-bans-2025/

## Apps

Map: https://thisismattmiller.github.io/book-bans-2025/apps/map/dist/

Book Browser: https://thisismattmiller.github.io/book-bans-2025/apps/explore/dist/

Subject by Geo: https://thisismattmiller.github.io/book-bans-2025/apps/by_state/dist/


## Data Files

### Primary Data Outputs

- **[data/books_by_title.json](data/books_by_title.json)** - Database of banned books indexed by ID, containing comprehensive metadata including ISBNs, OCLC numbers, subjects, descriptions, and ban information by district
- **[data/books_by_district.json](data/books_by_district.json)** - Books organized by school district (State - District format) with arrays of banned titles and ban details
- **[data/school_districts.json](data/school_districts.json)** - Complete school district information including Wikidata QIDs, NCES IDs, addresses, demographics, and county GeoJSON data
- **[data/refined_data_all.csv](data/refined_data_all.csv)** - Consolidated CSV combining all enriched data from multiple reconciliation passes

### Intermediate Data Files

- **[data/school_districts_with_qids.csv](data/school_districts_with_qids.csv)** - School districts with Wikidata QIDs and NCES IDs
- **[data/mil_bases.json](data/mil_bases.json)** - Geolocation data for military bases from Google Places API

## Scripts

### Data Preparation

#### [scripts/extract_parenthetical.py](scripts/extract_parenthetical.py)
Extracts parenthetical text from book titles and creates a separate `title_parenthetical` column.

**Usage:**
```bash
python scripts/extract_parenthetical.py <input_csv> <output_csv>
```

**Purpose:** Normalizes titles by separating parenthetical information (often series info or format details) for better matching.

---

#### [scripts/filter_unreconciled.py](scripts/filter_unreconciled.py)
Filters rows from `refined_data_pass_one.csv` that lack Mode Title values, creating `refined_data_pass_two.csv` for secondary reconciliation.

**Purpose:** Identifies books that need additional reconciliation passes to find metadata.

---

### School District Enrichment

#### [scripts/find_nces.py](scripts/find_nces.py)
Searches Wikidata for school districts and matches them by state, adding Wikidata QIDs and NCES IDs.

**Input:** `data/school_districts.csv`
**Output:** `data/school_districts_with_qids.csv`

**Purpose:** Enriches school district data with authoritative identifiers from Wikidata and NCES.

---

#### [scripts/find_nces_data.py](scripts/find_nces_data.py)
Scrapes detailed district data from NCES website and combines it with CSV data into a comprehensive JSON file.

**Input:** `data/school_districts_with_qids.csv`
**Output:** `data/school_districts.json`

**Purpose:** Pulls complete district information including addresses, phone numbers, student counts, financial data, and locale information.

---

#### [scripts/add_geojson.py](scripts/add_geojson.py)
Adds county GeoJSON data to school districts based on NCES County ID matching to county GEOID10.

**Input:**
- `data/school_districts.json`
- `/Users/m/Downloads/county.geo.json` (hardcoded path)

**Output:** Updates `data/school_districts.json` with county boundary data

**Purpose:** Enables geographic visualization of school districts using county-level boundaries.

---

#### [scripts/mil_base_geo.py](scripts/mil_base_geo.py)
Fetches geolocation data for military bases using Google Places API.

**Requirements:** `GOOGLE_PLACES_API_KEY` environment variable
**Output:** `data/mil_bases.json`

**Purpose:** Provides location data for military installations, which often have associated schools with book bans.

---

### Book Metadata Enrichment

#### [scripts/enrich_mode_titles.py](scripts/enrich_mode_titles.py)
Enriches `refined_data_pass_one.csv` with Mode Title data from `refined_data_pass_two_enriched.csv` for rows missing this data.

**Input:**
- `data/refined_data_pass_one.csv`
- `data/refined_data_pass_two_enriched.csv`

**Output:** `data/refined_data_all.csv`

**Purpose:** Backfills missing canonical title information from secondary reconciliation pass.

---

#### [scripts/gb_reconcile.py](scripts/gb_reconcile.py)
Finds books without ISBNs, queries Google Books API, validates matches using Gemini AI, and updates records.

**Requirements:** `GEMINI_API_KEY` environment variable
**Input/Output:** `data/books_by_title.json` (updates in place)

**Purpose:** Uses AI to intelligently match and validate book metadata from Google Books when ISBNs are missing.

---

#### [scripts/add_oclc_and_subjects.py](scripts/add_oclc_and_subjects.py)
Searches WorldCat by ISBN for books without OCLC numbers and populates OCLC numbers, subjects, classifications, and other metadata.

**Requirements:**
- `OCLC_CLIENT_ID` environment variable
- `OCLC_SECRET` environment variable

**Input/Output:** `data/books_by_title.json` (updates in place)

**Purpose:** Enriches book metadata with authoritative library data from WorldCat/OCLC.

---

#### [scripts/get_holdings_count.py](scripts/get_holdings_count.py)
Queries WorldCat holdings endpoint to get library holdings counts and editions information for books with OCLC numbers.

**Requirements:**
- `OCLC_CLIENT_ID` environment variable
- `OCLC_SECRET` environment variable

**Input/Output:** `data/books_by_title.json` (updates in place)

**Purpose:** Determines how widely held each banned book is across libraries, indicating popularity and availability.

---

#### [scripts/clean_subjects.py](scripts/clean_subjects.py)
Cleans subject headings using Google Gemini API by removing non-English subjects, format-based subjects (like "AUDIOBOOK"), and consolidating duplicates.

**Requirements:** `GEMINI_API_KEY` environment variable
**Input/Output:** `data/books_by_title.json` (updates in place)

**Purpose:** Normalizes subject headings by removing format/audience qualifiers and creating clean content-based subjects.

---

#### [scripts/backfill_data_from_second_pass.py](scripts/backfill_data_from_second_pass.py)
Backfills missing metadata (ISBNs, descriptions, subjects) from `refined_data_pass_two_enriched.csv` into `books_by_title.json` by matching on title and author.

**Purpose:** Ensures no metadata is lost between different processing passes.

---

### Data Transformation

#### [scripts/collapse_data.py](scripts/collapse_data.py)
Collapses `refined_data_all.csv` into two optimized JSON structures:
1. Books indexed by title with ban arrays
2. Books indexed by district with title arrays

**Input:** `data/refined_data_all.csv`
**Output:**
- `data/books_by_title.json`
- `data/books_by_district.json`

**Purpose:** Creates structured, queryable data formats for both book-centric and district-centric analysis.

---

#### [scripts/build_dist_data.py](scripts/build_dist_data.py)
Builds a minimal, optimized data array for the web interface from the full `books_by_title.json`. Calculates popularity tiers based on holdings statistics.

**Input:** `data/books_by_title.json`
**Output:** `apps/public/data.json`

**Purpose:** Creates a lightweight data file for frontend applications with computed popularity metrics.

---


### Utility Scripts

#### [scripts/no_match.py](scripts/no_match.py)
Lists all books without ISBNs for quality control and manual review.

**Usage:**
```bash
python scripts/no_match.py
```

---

#### [scripts/no_oclc.py](scripts/no_oclc.py)
Lists all books without OCLC numbers for quality control and manual review.

**Usage:**
```bash
python scripts/no_oclc.py
```

---

## Typical Processing Pipeline

1. Extract and clean titles: `extract_parenthetical.py`
2. Enrich school districts: `find_nces.py` → `find_nces_data.py` → `add_geojson.py`
3. First reconciliation pass (external tools)
4. Filter unreconciled: `filter_unreconciled.py`
5. Second reconciliation pass (external tools)
6. Merge reconciliation data: `enrich_mode_titles.py`
7. Collapse to JSON: `collapse_data.py`
8. Enrich with Google Books: `gb_reconcile.py`
9. Add OCLC data: `add_oclc_and_subjects.py`
10. Get holdings counts: `get_holdings_count.py`
11. Clean subjects: `clean_subjects.py`
12. Backfill missing data: `backfill_data_from_second_pass.py`
13. Download covers: `download_thumbs.py`
14. Build distribution data: `build_dist_data.py`

## Dependencies

- Python 3.x
- `requests` - HTTP library
- `google-genai` - Google Gemini AI API
- `Pillow` (PIL) - Image processing

## Environment Variables

- `GOOGLE_PLACES_API_KEY` - For military base geolocation
- `GEMINI_API_KEY` - For AI-powered reconciliation and subject cleaning
- `OCLC_CLIENT_ID` - For WorldCat API access
- `OCLC_SECRET` - For WorldCat API access

## License

MIT License - See [LICENSE](LICENSE) file for details
