# NWIS (Nearby Wells Intelligence System)

A lightweight, beginner-friendly prototype designed to search, score, and analyze historical drilling events and incidents from nearby offset wells based on drilling depth, geological formation, and optional event types.

---

## 📁 Project Structure

```text
nwis-historical-intelligence/
├── .env
├── .gitignore
├── nwis_mock_historical_events.json
├── src/
│   ├── analyzer.py
│   ├── data_loader.py
│   ├── evidence.py
│   ├── intelligence.py
│   ├── main.py
│   ├── search.py
│   └── llm/
│       ├── __init__.py
│       ├── answer_generator.py
│       ├── base.py
│       ├── gemini.py
│       ├── query_parser.py
│       └── query_service.py
├── test_answer_generator.py
├── test_end_to_end.py
├── test_llm.py
├── test_query_parser.py
├── test_query_service.py
└── README.md
```

---

## 🔍 Module Responsibilities

- **`nwis_mock_historical_events.json`**:
  The source dataset containing historical drilling event records (well ID, depth, formation, incident type, cause, mitigation, and outcome).
- **`src/data_loader.py`**:
  Contains `load_historical_events(file_path)` to safely load and parse the JSON dataset.
- **`src/search.py`**:
  Contains `search_historical_events(...)` which filters events based on well IDs, formation, depth window ($current\_depth \pm depth\_tolerance$), and optional event type. Calculates depth difference and relevance score, returning results sorted by relevance.
- **`src/analyzer.py`**:
  Contains `analyze_historical_events(results)` which calculates aggregated statistics: total events, unique wells, event frequencies, most common event, depth range, average depth, cause frequencies, and mitigation frequencies.
- **`src/evidence.py`**:
  Contains `generate_evidence(results, current_depth, formation)` which produces deterministic, traceable evidence records directly from existing historical event fields and report IDs without relying on external models or ungrounded claims.
- **`src/llm/`**:
  Provider-independent LLM abstraction & explanation layer:
  - `base.py`: Defines the abstract `LLMProvider` interface with `.generate(prompt: str) -> str`.
  - `gemini.py`: Implements `GeminiProvider` using Google's official `google-genai` SDK. Automatically loads configuration (`GEMINI_API_KEY`, `GEMINI_MODEL`) from the root `.env` file via `python-dotenv`, while preserving externally set environment variables.
  - `query_parser.py`: Implements `LLMQueryParser`, translating natural language drilling queries strictly into structured search parameters (`current_depth`, `formation`, `event_type`, `depth_tolerance`) without retrieving data or hallucinating facts.
  - `query_service.py`: Implements `HistoricalQueryService`, connecting the query parser to the deterministic `analyze_well()` engine and enforcing required parameter validation (`current_depth` and `formation`).
  - `answer_generator.py`: Implements `HistoricalAnswerGenerator`, producing grounded, concise engineer summaries based strictly on the deterministic `analyze_well()` intelligence output.
- **`src/intelligence.py`**:
  Contains `analyze_well(...)`, the **main public entry point** of the Historical Intelligence Engine. It coordinates the search, pattern analysis, and evidence generation modules and returns a single unified dictionary containing `historical_events`, `pattern_analysis`, and `evidence`.
- **`src/main.py`**:
  The interactive entry point prompting for search parameters, calling `analyze_well()`, and clearly displaying relevant events, pattern analysis summary, and historical evidence.
- **`test_llm.py`**:
  Test script to verify LLM provider initialization, configuration, and inference.
- **`test_query_parser.py`**:
  Test script to verify natural language query parsing, markdown code block stripping, and validation using mock LLM responses.
- **`test_query_service.py`**:
  Integration test script verifying that parsed questions trigger the deterministic intelligence pipeline and return structured results.
- **`test_answer_generator.py`**:
  Unit test script verifying grounded explanation generation and prompt constraints against hallucination.
- **`test_end_to_end.py`**:
  End-to-end Copilot pipeline test using the live `GeminiProvider` for natural-language query understanding and grounded answer generation.

---

## 📦 Requirements & Installation


### Required Packages
- **`python-dotenv`**: Loads environment variables from the `.env` file.
- **`google-genai`**: Official Google GenAI SDK for Gemini models.

### Installation Instructions

#### Option 1: Direct Install
Run the following in your terminal:
```bash
pip install python-dotenv google-genai
```

#### Option 2: Using a Virtual Environment (Recommended)
1. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\activate

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the dependencies:
   ```bash
   pip install python-dotenv google-genai
   ```

---

## ⚙️ Configuration & Environment

The project automatically loads Gemini configuration from the root `.env` file:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```
Alternatively, externally set system environment variables are also supported.

---

## 🚀 How to Run

### Prerequisites
- Python 3.x
- Required third-party packages: `python-dotenv`, `google-genai`

### Run from project directory (without LLM, absolutely basic: full python)
Navigate to the project root and run:

```bash
python src/main.py
```

Or from inside the `src/` directory:

```bash
cd src
python main.py
```

### 2. Run Tests
- **Core Unit / Integration Tests (no API key required)**:
  ```bash
  python test_query_parser.py
  python test_query_service.py
  python test_answer_generator.py
  ```
- **Live LLM Tests (requires `GEMINI_API_KEY` & installed packages)**:
  ```bash
  python test_llm.py
  python test_end_to_end.py
  ```
