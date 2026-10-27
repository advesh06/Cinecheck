# CineCheck Dataset Documentation & Data Integrity Notice

## Overview
This directory contains reference and benchmark datasets designed for the **CineCheck** Fake Movie Review Detection System, covering Indian theatrical releases and major international titles scheduled between **1 January 2025 and 30 September 2026**.

## Data Integrity & Ethical Compliance
In accordance with ethical AI guidelines, platform Terms of Service, and academic integrity policies:
1. **Simulation Transparency:** Real BookMyShow user account profiles and private review records are **not** harvested or scraped without explicit authorization.
2. **Synthetic & Curated Benchmark:** The primary development dataset (`cinecheck_reviews.csv`) contains carefully curated synthetic demonstration reviews modeled upon authentic BookMyShow review linguistics, sentiment patterns, promotional astroturfing techniques, and community critiques.
3. **Ground-Truth Labelling Standards:** Labels (`fake` and `genuine`) exist **only** for curated benchmark training and evaluation sets. Unlabelled reviews in subsequent uploads are never assigned synthetic ground-truth labels; model predictions are strictly distinguished as probabilistic inference rather than definitive verdicts.
4. **Platform Representation:** The source field explicitly marks synthetic samples as `synthetic_bms_simulation` or `twsma_benchmark_2025_2026`.

## Schema Specification

Every review file (`CSV` or `XLSX`) accepted by CineCheck must conform to the following schema:

| Column Header | Data Type | Description | Required | Example Values |
|---|---|---|---|---|
| `review_id` | String / Integer | Unique identifier for the review | Yes | `REV-2025-001`, `REV-2025-142` |
| `movie_title` | String | Title of the movie listed on BookMyShow | Yes | `Chhaava`, `Game Changer`, `War 2` |
| `movie_release_date` | Date (YYYY-MM-DD) | Confirmed or announced theatrical release date | Yes | `2025-02-14`, `2025-01-10` |
| `review_date` | Date (YYYY-MM-DD) | Date the review was submitted | Yes | `2025-02-15`, `2025-02-20` |
| `review_text` | Text | Full text content of the review | Yes | `"Vicky Kaushal delivers a roaring performance..."` |
| `rating` | Float / Integer | Star rating assigned by reviewer (1.0 to 5.0) | Yes | `4.5`, `1.0`, `5.0` |
| `label` | String (`fake` / `genuine` / blank) | Ground-truth benchmark label (optional for raw uploads) | No | `genuine`, `fake`, `""` |
| `source` | String | Data origin or collection tag | Yes | `synthetic_bms_simulation`, `bookmyshow_sample` |

## Verified Theatrical Releases (2025 – 2026 Window)
- **Chhaava** (Release Date: 2025-02-14)
- **Game Changer** (Release Date: 2025-01-10)
- **Fateh** (Release Date: 2025-01-10)
- **Deva** (Release Date: 2025-01-31)
- **Sky Force** (Release Date: 2025-01-24)
- **Dhadak 2** (Release Date: 2025-02-21)
- **Captain America: Brave New World** (Release Date: 2025-02-14)
- **The Raja Saab** (Release Date: 2025-04-10)
- **Toxic: A Fairy Tale for Grown-ups** (Release Date: 2025-04-10)
- **Mission: Impossible – The Final Reckoning** (Release Date: 2025-05-23)
- **Housefull 5** (Release Date: 2025-06-06)
- **Superman** (Release Date: 2025-07-11)
- **War 2** (Release Date: 2025-08-14)
- **Kantara: Chapter 1** (Release Date: 2025-10-02)
- **Avatar: Fire and Ash** (Release Date: 2025-12-19)

## Known Dataset Limitations
1. Synthetic linguistic patterns may not capture subtle sarcasm, regional multilingual slang (Hinglish/Tanglish), or evasive adversarial bots.
2. The initial baseline classifier trained on this benchmark is an academic demonstration model. It should not be used as legal or conclusive proof of fraud.
