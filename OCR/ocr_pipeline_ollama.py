"""
GeoMine OCR Pipeline v3.0 — Enterprise-Grade Document Ingestion
================================================================
A production-grade, fully offline OCR pipeline for extracting structured
drilling data from PDF reports using a local LLM (Ollama).

Features:
  Tier 1: Schema enforcement, duplicate detection, document classification,
          audit trail, FastAPI integration
  Tier 2: Table-aware extraction, image pre-processing, batch mode + CSV,
          multi-format support (PDF, DOCX, XLSX, images)
  Tier 3: India coordinate cross-validation, threaded queue, correction API

Usage:
  python OCR/ocr_pipeline_ollama.py                      # Test mode (no DB)
  python OCR/ocr_pipeline_ollama.py --insert              # Extract + insert to DB
  python OCR/ocr_pipeline_ollama.py --batch --insert      # Batch + CSV export
"""

import os
import csv
import json
import hashlib
import sys
import threading
import queue
import requests
import pymupdf
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "phi3")
PIPELINE_VERSION = "3.0"

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "nwis_wells_db"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}

# ---------------------------------------------------------------------------
# SCHEMA DEFINITIONS (Tier 1: Strict Schema Enforcement)
# ---------------------------------------------------------------------------
DRILLING_EVENT_SCHEMA = {
    "well_id": str,
    "latitude": float,
    "longitude": float,
    "event_depth": float,
    "event_type": str,
    "formation": str,
    "npt_duration_minutes": int,
    "npt_category": str,
    "summary": str,
}

INFRASTRUCTURE_SCHEMA = {
    "infra_id": str,
    "latitude": float,
    "longitude": float,
    "depth_m": float,
    "infra_type": str,
}

KNOWN_EVENT_TYPES = [
    "Stuck Pipe", "Mud Loss", "Kick", "Wellbore Instability",
    "Equipment Failure", "BHA Failure", "Torque Spike",
    "Severe Mud Loss", "Partial Mud Loss", "Gas Cut Mud",
    "Tight Hole", "Pack Off", "Twist Off", "Fishing",
    "Lost Circulation", "Well Control", "Casing Damage",
    "Cementing Failure", "BOP Test Failure", "Normal", "Completion",
    "Discovery", "Blowout", "H2S Release",
]

KNOWN_INFRA_TYPES = [
    "Aquifer", "Pipeline", "Cable", "Foundation", "Tunnel",
    "Offshore Drilling Rig", "Subsea Pipeline",
]

VALID_DOC_CLASSES = [
    "drilling_report", "completion_report", "incident_report",
    "annual_report", "procurement", "other",
]

# Validation ranges
LAT_RANGE = (-90.0, 90.0)
LON_RANGE = (-180.0, 180.0)
DEPTH_RANGE = (0.0, 15000.0)
NPT_RANGE = (0, 10080)

# Tier 3: India bounding box for cross-validation
INDIA_LAT = (6.5, 37.0)
INDIA_LON = (68.0, 97.5)

# Sanitization junk values
JUNK_VALUES = {"null", "unknown", "not provided", "n/a", "none", "-", "",
               "not specified", "not specified in the report"}


# ===================================================================
# TIER 1: CORE PIPELINE
# ===================================================================

# ---------------------------------------------------------------------------
# 1. FILE HASHING (Duplicate Detection)
# ---------------------------------------------------------------------------
def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 hash from raw bytes (for API uploads)."""
    return hashlib.sha256(data).hexdigest()


def is_duplicate(file_hash: str, insert_to_db: bool) -> bool:
    """Check if a file with this hash has already been processed."""
    if not insert_to_db:
        return False
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM processed_files WHERE file_hash = %s", (file_hash,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        return exists
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 2. TEXT EXTRACTION (PDF, DOCX, XLSX, Images)
# ---------------------------------------------------------------------------
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from PDF. Uses native text first, tables second, OCR fallback."""
    full_text = ""
    try:
        doc = pymupdf.open(str(pdf_path))
        for page_num, page in enumerate(doc, 1):
            page_text = page.get_text()

            # Tier 2: Table-aware extraction
            try:
                tables = page.find_tables()
                for table in tables:
                    df = table.to_pandas()
                    table_str = df.to_string(index=False)
                    page_text += f"\n[TABLE on page {page_num}]\n{table_str}\n"
            except Exception:
                pass  # find_tables not available or no tables

            # Fallback: scanned image pages
            if not page_text.strip():
                page_text = _ocr_page(page)

            full_text += page_text + "\n"
    except Exception as e:
        print(f"  [ERROR] Failed to read PDF: {e}")
    return full_text


def _ocr_page(page) -> str:
    """OCR a single page with image pre-processing (Tier 2)."""
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter

        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Tier 2: Image pre-processing for better OCR accuracy
        img = img.convert("L")                                    # Grayscale
        img = ImageEnhance.Contrast(img).enhance(2.0)             # Boost contrast
        img = img.filter(ImageFilter.SHARPEN)                     # Sharpen edges
        img = img.point(lambda x: 0 if x < 140 else 255, '1')    # Binarize

        return pytesseract.image_to_string(img)
    except ImportError:
        return ""
    except Exception:
        return ""


def extract_text_from_docx(file_path: Path) -> str:
    """Tier 2: Extract text from Word documents."""
    try:
        import docx
        doc = docx.Document(str(file_path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        # Also extract tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                paragraphs.append(row_text)
        return "\n".join(paragraphs)
    except ImportError:
        print("  [ERROR] python-docx not installed. Run: pip install python-docx")
        return ""
    except Exception as e:
        print(f"  [ERROR] Failed to read DOCX: {e}")
        return ""


def extract_text_from_xlsx(file_path: Path) -> str:
    """Tier 2: Extract text from Excel spreadsheets."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(file_path), read_only=True)
        all_text = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                row_text = " | ".join(str(c) for c in row if c is not None)
                if row_text.strip():
                    all_text.append(row_text)
        return "\n".join(all_text)
    except ImportError:
        print("  [ERROR] openpyxl not installed. Run: pip install openpyxl")
        return ""
    except Exception as e:
        print(f"  [ERROR] Failed to read XLSX: {e}")
        return ""


def extract_text_from_image(file_path: Path) -> str:
    """Tier 2: Extract text from images (JPG, PNG, TIFF)."""
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter

        img = Image.open(str(file_path))
        # Pre-processing
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)

        return pytesseract.image_to_string(img)
    except ImportError:
        print("  [ERROR] pytesseract not installed.")
        return ""
    except Exception as e:
        print(f"  [ERROR] Failed to read image: {e}")
        return ""


def extract_text(file_path: Path) -> str:
    """Tier 2: Universal text extractor — routes to the right parser by extension."""
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext in (".xlsx", ".xls"):
        return extract_text_from_xlsx(file_path)
    elif ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"):
        return extract_text_from_image(file_path)
    else:
        # Try reading as plain text
        try:
            return file_path.read_text(errors="ignore")
        except Exception:
            print(f"  [ERROR] Unsupported format: {ext}")
            return ""


# ---------------------------------------------------------------------------
# 3. TEXT CHUNKING
# ---------------------------------------------------------------------------
def chunk_text(text: str, max_chars: int = 12000) -> list:
    """Cap and chunk text for LLM processing."""
    text = text[:15000]
    if len(text) <= max_chars:
        return [text]
    chunks, overlap, start = [], 500, 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# 4. DOCUMENT CLASSIFICATION (Tier 1)
# ---------------------------------------------------------------------------
def classify_document(raw_text: str) -> str:
    """Ask the local LLM to classify the document type before extraction."""
    sample = raw_text[:3000]

    prompt = f"""Classify this document into exactly one of these categories:
- drilling_report
- completion_report
- incident_report
- annual_report
- procurement
- other

Return ONLY a JSON object with one key "document_class" and the category as its value.

Document text:
{sample}
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        body = resp.json().get("response", "{}")
        result = json.loads(body)
        doc_class = result.get("document_class", "other")
        if doc_class not in VALID_DOC_CLASSES:
            doc_class = "other"
        return doc_class
    except Exception:
        return "other"


# ---------------------------------------------------------------------------
# 5. LLM EXTRACTION
# ---------------------------------------------------------------------------
def parse_with_local_llm(raw_text: str) -> dict:
    """Send text to the local Ollama LLM and get structured JSON back."""

    prompt = f"""You are a Drilling Report Data Extraction AI.

Extract data from the report text into a JSON object with exactly two keys.

1. "drilling_event" with EXACTLY these fields (no others):
   - well_id (string or null)
   - latitude (float or null)
   - longitude (float or null)
   - event_depth (float in meters, or null)
   - event_type (string or null)
   - formation (string or null)
   - npt_duration_minutes (integer or null)
   - npt_category (string or null)
   - summary (string, one sentence summary of the incident, or null)

2. "infrastructure" with EXACTLY these fields (no others):
   - infra_id (string or null)
   - latitude (float or null)
   - longitude (float or null)
   - depth_m (float or null)
   - infra_type (string or null)

RULES:
- Return ONLY the fields listed above. Do not add any extra fields.
- If a value is not found, return null (the JSON keyword, not a string).
- Numeric fields MUST be raw numbers with no units attached.
- Convert coordinates from DMS (degrees/minutes/seconds) to decimal degrees.
- Do NOT hallucinate or invent data that is not in the text.

Report Text:
{raw_text}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
        resp.raise_for_status()
        body = resp.json().get("response", "{}")
        return json.loads(body)
    except requests.ConnectionError:
        print(f"  [ERROR] Cannot reach Ollama at {OLLAMA_URL}. Is it running?")
        return {}
    except json.JSONDecodeError:
        print(f"  [ERROR] LLM returned invalid JSON.")
        return {}
    except Exception as e:
        print(f"  [ERROR] LLM call failed: {e}")
        return {}


# ---------------------------------------------------------------------------
# 6. STRICT SCHEMA ENFORCEMENT (Tier 1)
# ---------------------------------------------------------------------------
def enforce_schema(data: dict, schema: dict) -> dict:
    """Strip hallucinated fields and cast to correct types."""
    enforced = {}
    for field, expected_type in schema.items():
        val = data.get(field)

        # Sanitize junk strings
        if isinstance(val, str) and val.strip().lower() in JUNK_VALUES:
            val = None

        # Type casting
        if val is not None:
            try:
                if expected_type == float:
                    val = float(val)
                elif expected_type == int:
                    val = int(float(val))  # int("240.0") fails, so cast via float
                elif expected_type == str:
                    val = str(val).strip()
                    if not val:
                        val = None
            except (ValueError, TypeError):
                val = None

        enforced[field] = val
    return enforced


# ---------------------------------------------------------------------------
# 7. DATA VALIDATION
# ---------------------------------------------------------------------------
def _validate_numeric(value, name, valid_range, warnings):
    """Validate a numeric field against a range."""
    if value is None:
        return
    try:
        v = float(value)
        if not (valid_range[0] <= v <= valid_range[1]):
            warnings.append(f"{name} {v} out of range {valid_range}")
    except (ValueError, TypeError):
        warnings.append(f"{name} '{value}' is not a valid number")


def validate_event(event: dict) -> tuple:
    """Validate extracted drilling event. Returns (is_valid, warnings)."""
    warnings = []

    _validate_numeric(event.get("latitude"), "Latitude", LAT_RANGE, warnings)
    _validate_numeric(event.get("longitude"), "Longitude", LON_RANGE, warnings)
    _validate_numeric(event.get("event_depth"), "Depth", DEPTH_RANGE, warnings)
    _validate_numeric(event.get("npt_duration_minutes"), "NPT", NPT_RANGE, warnings)

    et = event.get("event_type")
    if et and et not in KNOWN_EVENT_TYPES:
        warnings.append(f"Event type '{et}' not in known list (will still insert)")

    # Tier 3: India cross-validation
    lat = event.get("latitude")
    lon = event.get("longitude")
    if lat is not None and lon is not None:
        if not (INDIA_LAT[0] <= lat <= INDIA_LAT[1] and INDIA_LON[0] <= lon <= INDIA_LON[1]):
            warnings.append(f"Coordinates ({lat}, {lon}) are outside India's bounding box")

    usable = sum(1 for v in event.values() if v is not None)
    is_valid = usable >= 2
    return is_valid, warnings


def validate_infra(infra: dict) -> tuple:
    """Validate extracted infrastructure. Returns (is_valid, warnings)."""
    warnings = []

    _validate_numeric(infra.get("latitude"), "Infra Lat", LAT_RANGE, warnings)
    _validate_numeric(infra.get("longitude"), "Infra Lon", LON_RANGE, warnings)
    _validate_numeric(infra.get("depth_m"), "Infra Depth", DEPTH_RANGE, warnings)

    it = infra.get("infra_type")
    if it and it not in KNOWN_INFRA_TYPES:
        warnings.append(f"Infra type '{it}' not in known list (will still insert)")

    # Tier 3: India cross-validation
    lat = infra.get("latitude")
    lon = infra.get("longitude")
    if lat is not None and lon is not None:
        if not (INDIA_LAT[0] <= lat <= INDIA_LAT[1] and INDIA_LON[0] <= lon <= INDIA_LON[1]):
            warnings.append(f"Infra coordinates ({lat}, {lon}) outside India's bounding box")

    usable = sum(1 for v in infra.values() if v is not None)
    is_valid = usable >= 2
    return is_valid, warnings


# ---------------------------------------------------------------------------
# 8. CONFIDENCE SCORING
# ---------------------------------------------------------------------------
def confidence_score(data: dict, schema: dict) -> float:
    """Calculate confidence based on schema fields only (ignores hallucinated fields)."""
    total = len(schema)
    if total == 0:
        return 0.0
    filled = sum(1 for k in schema if data.get(k) is not None)
    return round((filled / total) * 100, 1)


# ---------------------------------------------------------------------------
# 9. DATABASE OPERATIONS
# ---------------------------------------------------------------------------
def get_db_connection():
    import psycopg2
    return psycopg2.connect(**DB_CONFIG)


def record_processed_file(file_name, file_hash, file_size, doc_class,
                          event_conf, infra_conf, status, warnings_list):
    """Record a processed file in the duplicate detection table."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO processed_files
                (file_name, file_hash, file_size_bytes, document_class,
                 event_confidence, infra_confidence, status, warnings)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (file_hash) DO NOTHING;
        """, (file_name, file_hash, file_size, doc_class,
              event_conf, infra_conf, status,
              json.dumps(warnings_list) if warnings_list else None))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  [DB WARN] Could not record processed file: {e}")


def insert_drilling_event(event: dict, source_file: str, file_hash: str,
                          doc_class: str, confidence: float) -> int:
    """Insert a validated drilling event with full audit trail."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO historical_drilling_events
                (well_id, latitude, longitude, event_depth, event_type,
                 formation, npt_duration_minutes, npt_category, summary_text,
                 source_file, file_hash, document_class, extraction_confidence, processed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            event.get("well_id"),
            event.get("latitude"),
            event.get("longitude"),
            event.get("event_depth"),
            event.get("event_type"),
            event.get("formation"),
            event.get("npt_duration_minutes"),
            event.get("npt_category"),
            event.get("summary"),
            source_file, file_hash, doc_class, confidence, datetime.utcnow(),
        ))
        row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    except Exception as e:
        conn.rollback()
        print(f"  [DB ERROR] {e}")
        return -1
    finally:
        cur.close()
        conn.close()


def insert_infrastructure(infra: dict, source_file: str, file_hash: str,
                          doc_class: str, confidence: float) -> int:
    """Insert a validated infrastructure record with full audit trail."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO underground_infrastructure
                (infra_id, latitude, longitude, depth_m, infra_type,
                 source_file, file_hash, document_class, extraction_confidence, processed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            infra.get("infra_id"),
            infra.get("latitude"),
            infra.get("longitude"),
            infra.get("depth_m"),
            infra.get("infra_type"),
            source_file, file_hash, doc_class, confidence, datetime.utcnow(),
        ))
        row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    except Exception as e:
        conn.rollback()
        print(f"  [DB ERROR] {e}")
        return -1
    finally:
        cur.close()
        conn.close()


# ===================================================================
# TIER 2: BATCH PROCESSING + CSV EXPORT
# ===================================================================

def export_results_to_csv(results: list, output_path: Path):
    """Export all extraction results to a CSV file."""
    if not results:
        return

    fieldnames = [
        "file", "status", "document_class", "event_confidence", "infra_confidence",
        "well_id", "latitude", "longitude", "event_depth", "event_type",
        "formation", "npt_duration_minutes", "npt_category", "summary",
        "infra_id", "infra_lat", "infra_lon", "infra_depth_m", "infra_type",
        "warnings", "db_event_id", "db_infra_id",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for r in results:
            event = r.get("drilling_event") or {}
            infra = r.get("infrastructure") or {}
            row = {
                "file": r["file"],
                "status": r["status"],
                "document_class": r.get("document_class", ""),
                "event_confidence": r["event_confidence"],
                "infra_confidence": r["infra_confidence"],
                "well_id": event.get("well_id"),
                "latitude": event.get("latitude"),
                "longitude": event.get("longitude"),
                "event_depth": event.get("event_depth"),
                "event_type": event.get("event_type"),
                "formation": event.get("formation"),
                "npt_duration_minutes": event.get("npt_duration_minutes"),
                "npt_category": event.get("npt_category"),
                "summary": event.get("summary"),
                "infra_id": infra.get("infra_id"),
                "infra_lat": infra.get("latitude"),
                "infra_lon": infra.get("longitude"),
                "infra_depth_m": infra.get("depth_m"),
                "infra_type": infra.get("infra_type"),
                "warnings": "; ".join(r.get("warnings", [])),
                "db_event_id": r.get("db_event_id"),
                "db_infra_id": r.get("db_infra_id"),
            }
            writer.writerow(row)

    print(f"\n  [CSV] Results exported to {output_path}")


# ===================================================================
# TIER 3: THREADED PROCESSING QUEUE
# ===================================================================

class ProcessingQueue:
    """Simple threaded queue for non-blocking file processing."""

    def __init__(self, insert_to_db=False, max_workers=2):
        self._queue = queue.Queue()
        self._results = []
        self._lock = threading.Lock()
        self._insert_to_db = insert_to_db
        self._workers = []

        for _ in range(max_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._workers.append(t)

    def _worker(self):
        while True:
            try:
                file_path = self._queue.get(timeout=1)
            except queue.Empty:
                continue
            if file_path is None:
                break
            result = process_single_file(file_path, insert_to_db=self._insert_to_db)
            with self._lock:
                self._results.append(result)
            self._queue.task_done()

    def submit(self, file_path: Path):
        self._queue.put(file_path)

    def wait_and_get_results(self) -> list:
        self._queue.join()
        return list(self._results)

    def shutdown(self):
        for _ in self._workers:
            self._queue.put(None)
        for t in self._workers:
            t.join(timeout=5)


# ===================================================================
# MAIN PIPELINE
# ===================================================================

def process_single_file(file_path: Path, insert_to_db: bool = False,
                        file_bytes: bytes = None) -> dict:
    """Process a single file through the full enterprise pipeline."""
    result = {
        "file": file_path.name,
        "status": "SKIPPED",
        "document_class": None,
        "drilling_event": None,
        "infrastructure": None,
        "event_confidence": 0.0,
        "infra_confidence": 0.0,
        "warnings": [],
        "db_event_id": None,
        "db_infra_id": None,
    }

    # --- Step 1: File hashing + duplicate detection ---
    if file_bytes:
        file_hash = compute_bytes_hash(file_bytes)
        file_size = len(file_bytes)
    else:
        file_hash = compute_file_hash(file_path)
        file_size = file_path.stat().st_size

    if is_duplicate(file_hash, insert_to_db):
        result["status"] = "DUPLICATE"
        print(f"  [SKIP] Duplicate file detected (hash: {file_hash[:12]}...)")
        return result

    # --- Step 2: Extract text ---
    raw_text = extract_text(file_path)
    if not raw_text.strip():
        result["status"] = "NO_TEXT"
        result["warnings"].append("No text extracted from file")
        return result

    # --- Step 3: Document classification ---
    doc_class = classify_document(raw_text)
    result["document_class"] = doc_class
    print(f"  3. Document classified as: {doc_class}")

    if doc_class in ("procurement", "other"):
        result["status"] = "SKIPPED_CLASS"
        print(f"  [SKIP] Non-drilling document ({doc_class}). Skipping extraction.")
        if insert_to_db:
            record_processed_file(file_path.name, file_hash, file_size,
                                  doc_class, 0, 0, "SKIPPED", [])
        return result

    # --- Step 4: LLM extraction ---
    chunks = chunk_text(raw_text)
    best_event, best_infra = {}, {}

    for chunk in chunks:
        extracted = parse_with_local_llm(chunk)
        if not extracted:
            continue

        event = extracted.get("drilling_event",
                              extracted.get("historical_drilling_events", {}))
        infra = extracted.get("infrastructure",
                              extracted.get("underground_infrastructure", {}))

        if isinstance(event, list):
            event = event[0] if event else {}
        if isinstance(infra, list):
            infra = infra[0] if infra else {}

        if confidence_score(event, DRILLING_EVENT_SCHEMA) > confidence_score(best_event, DRILLING_EVENT_SCHEMA):
            best_event = event
        if confidence_score(infra, INFRASTRUCTURE_SCHEMA) > confidence_score(best_infra, INFRASTRUCTURE_SCHEMA):
            best_infra = infra

    # --- Step 5: Schema enforcement ---
    best_event = enforce_schema(best_event, DRILLING_EVENT_SCHEMA)
    best_infra = enforce_schema(best_infra, INFRASTRUCTURE_SCHEMA)

    e_conf = confidence_score(best_event, DRILLING_EVENT_SCHEMA)
    i_conf = confidence_score(best_infra, INFRASTRUCTURE_SCHEMA)

    result["drilling_event"] = best_event
    result["infrastructure"] = best_infra
    result["event_confidence"] = e_conf
    result["infra_confidence"] = i_conf

    # --- Step 6: Validation ---
    event_valid, event_warns = validate_event(best_event)
    infra_valid, infra_warns = validate_infra(best_infra)
    result["warnings"] = event_warns + infra_warns

    # --- Step 7: Database insertion ---
    if insert_to_db:
        if event_valid:
            row_id = insert_drilling_event(best_event, file_path.name,
                                           file_hash, doc_class, e_conf)
            if row_id > 0:
                result["db_event_id"] = row_id

        if infra_valid:
            row_id = insert_infrastructure(best_infra, file_path.name,
                                           file_hash, doc_class, i_conf)
            if row_id > 0:
                result["db_infra_id"] = row_id

        record_processed_file(file_path.name, file_hash, file_size, doc_class,
                              e_conf, i_conf, "PROCESSED", result["warnings"])

    result["status"] = "PROCESSED"
    return result


# ---------------------------------------------------------------------------
# CLI ENTRY POINT
# ---------------------------------------------------------------------------
def process_all_reports(insert_to_db: bool = False, batch_mode: bool = False):
    """Main entry point. Process all supported files in the OCR directory."""
    script_dir = Path(__file__).resolve().parent
    supported_ext = {".pdf", ".docx", ".xlsx", ".xls", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
    all_files = sorted(f for f in script_dir.iterdir()
                       if f.suffix.lower() in supported_ext)

    if not all_files:
        print(f"No supported files found in {script_dir}")
        return

    print(f"GeoMine OCR Pipeline v{PIPELINE_VERSION}")
    print(f"Model: {MODEL_NAME} | DB Insert: {'ON' if insert_to_db else 'OFF'} | Batch: {'ON' if batch_mode else 'OFF'}")
    print(f"Found {len(all_files)} file(s) to process.\n")

    results = []

    for idx, file_path in enumerate(all_files, 1):
        print(f"--------------------------------------------------")
        print(f"  [{idx}/{len(all_files)}] {file_path.name}")
        print(f"  1. Computing file hash...")
        print(f"  2. Extracting text...")

        try:
            result = process_single_file(file_path, insert_to_db=insert_to_db)
        except Exception as e:
            print(f"  [ERROR] Pipeline failed: {e}")
            result = {"file": file_path.name, "status": "ERROR",
                      "document_class": None, "drilling_event": None,
                      "infrastructure": None, "event_confidence": 0.0,
                      "infra_confidence": 0.0, "warnings": [str(e)],
                      "db_event_id": None, "db_infra_id": None}

        results.append(result)

        # Print results
        if result["status"] not in ("DUPLICATE", "SKIPPED_CLASS", "NO_TEXT", "ERROR"):
            event = result.get("drilling_event") or {}
            infra = result.get("infrastructure") or {}

            print(f"\n  [Drilling Event] Confidence: {result['event_confidence']}%")
            for k, v in event.items():
                print(f"    {k}: {v}")

            print(f"\n  [Infrastructure] Confidence: {result['infra_confidence']}%")
            for k, v in infra.items():
                print(f"    {k}: {v}")

        if result.get("warnings"):
            print(f"\n  [Warnings]")
            for w in result["warnings"]:
                print(f"    - {w}")

        if insert_to_db:
            eid = result.get("db_event_id")
            iid = result.get("db_infra_id")
            if eid and eid > 0:
                print(f"\n  [DB] Drilling event inserted -> id={eid}")
            if iid and iid > 0:
                print(f"  [DB] Infrastructure inserted -> id={iid}")

        print()

    # --- SUMMARY ---
    processed = sum(1 for r in results if r["status"] == "PROCESSED")
    skipped = sum(1 for r in results if r["status"] in ("SKIPPED", "SKIPPED_CLASS"))
    duplicates = sum(1 for r in results if r["status"] == "DUPLICATE")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    avg_conf = sum(r["event_confidence"] for r in results) / max(len(results), 1)
    total_warns = sum(len(r.get("warnings", [])) for r in results)
    db_inserts = sum(1 for r in results if r.get("db_event_id") and r["db_event_id"] > 0)

    print("==================================================")
    print("  PIPELINE SUMMARY")
    print("==================================================")
    print(f"  Version          : v{PIPELINE_VERSION}")
    print(f"  Total files      : {len(all_files)}")
    print(f"  Processed        : {processed}")
    print(f"  Skipped (class)  : {skipped}")
    print(f"  Duplicates       : {duplicates}")
    print(f"  Errors           : {errors}")
    print(f"  Avg Confidence   : {avg_conf:.1f}%")
    print(f"  Validation Warns : {total_warns}")
    if insert_to_db:
        print(f"  DB Inserts       : {db_inserts}")
    print("==================================================")

    # Tier 2: CSV export in batch mode
    if batch_mode:
        csv_path = script_dir / "extraction_results.csv"
        export_results_to_csv(results, csv_path)


if __name__ == "__main__":
    do_insert = "--insert" in sys.argv
    do_batch = "--batch" in sys.argv
    process_all_reports(insert_to_db=do_insert, batch_mode=do_batch)
