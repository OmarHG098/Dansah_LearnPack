# Dansah LearnPack - AI Agent Instructions

## Project Overview
Dansah_LearnPack is a bootcamp review analysis pipeline that scrapes testimonials from multiple platforms, aggregates them, and trains a multi-label text classification model to categorize reviews by topic (pricing, mentors, career support, etc.).

## Architecture & Data Flow

### 1. Data Ingestion Layer
**Purpose**: Scrape reviews from multiple platforms using Selenium and BeautifulSoup.

**Key Files**:
- `*_testimonials.py` (5 files: careerkarma, bootcamprankings, course_report, switchup, nps)
- Each scraper follows identical pattern: authentication → pagination → parsing → categorization

**Patterns**:
- Uses `.env` for credentials (CK_EMAIL, CK_PASSWORD pattern)
- Selenium with headless Chrome for JavaScript-heavy sites
- WebDriverWait with 15-second timeouts for element loading
- Calls `categorize_review()` from functions.py during scraping
- Output: `{platform}_reviews.csv` with Review + 16 binary category columns

### 2. Data Aggregation Layer
**File**: [combined_data.py](combined_data.py)

**Workflow**:
1. Load individual platform CSVs using `pull_reviews()` - extracts Review column + categories
2. Concatenate via `concat_dataframes()` into single dataset
3. Save to `combined_data.csv` for downstream ML tasks

**Key Detail**: `pull_reviews()` validates that Review + category columns exist before returning

### 3. ML Training Layer
**File**: [test.py](test.py) (currently the main training script)

**Process**:
- Load combined_data.csv with multi-label classification task
- Custom `ReviewDataset` class handles tokenization with max_len=128
- Uses HuggingFace transformers (AutoTokenizer, AutoModelForSequenceClassification)
- Binary cross-entropy loss for multi-label (16 categories)
- Model saved to `trained_model/` directory

## Category Schema

**16 Bootcamp Review Categories** (defined in [functions.py](functions.py)):
- **Topics**: OnlinePlatform, MentorsTeachers, ContentSyllabus, FullStack, DataScience, Cybersecurity
- **Career**: CareerSupport, Job Guarantee, Outcomes
- **Business**: Price, Scholarships
- **Platform-specific**: Rigobot, LearnPack

**Text Processing**:
- Bilingual (English/Spanish) support with unicode normalization
- Word boundary regex matching (`\b...\b`) for exact phrase detection
- Combined headline + body text for categorization

## Critical Developer Workflows

### Running the Full Pipeline
```bash
# 1. Scrape all platforms (requires .env with credentials)
python careerkarma_testimonials.py
python bootcamprankings_testimonials.py
python course_report_testimonials.py
python switchup_testimonials.py
python nps_testimonials.py

# 2. Aggregate data
python combined_data.py

# 3. Train model
python test.py
```

### Adding New Data Source
1. Create `{platform}_testimonials.py` following careerkarma pattern
2. Ensure output CSV has "Review" column + all 16 category columns
3. Update `combined_data.py` to import and process new source
4. Verify `pull_reviews()` correctly extracts required columns

### Modifying Categories
- Edit `categories` dict in [functions.py](functions.py) - keys are column names, values are keyword lists
- Both English and Spanish keywords supported
- Changes auto-propagate to all scrapers via `categorize_review()`

## Key Dependencies & Setup

**Environment Variables** (required for scrapers):
- CK_EMAIL, CK_PASSWORD - CareerKarma authentication
- Similar patterns for other platforms if implemented

**Python Packages**:
- Web: selenium, beautifulsoup4, webdriver-manager
- ML: transformers, torch, scikit-learn
- Data: pandas
- Config: python-dotenv

## File Responsibilities

| File | Purpose |
|------|---------|
| functions.py | Shared utilities: text normalization, categorization, dataframe concat |
| combined_data.py | Orchestrates data aggregation pipeline |
| test.py | ML model training (misnamed - should be model_training.py) |
| *_reviews.csv | Raw data from each platform |
| combined_data.csv | Aggregated dataset for training |
| trained_model/ | Serialized model artifacts (config.json, tokenizer, vocab) |

## Important Conventions

1. **CSV Structure**: All review CSVs must have "Review" column + exact 16 category columns
2. **Tokenizer**: Fixed max_length=128 - review text is truncated/padded to this length
3. **Scraper Headless Mode**: Remove `--headless=new` argument when debugging selectors
4. **Text Normalization**: Always apply `normalize_text()` before category matching
5. **Multi-label Task**: Each review can belong to multiple categories (not mutually exclusive)
