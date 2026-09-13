import os
import re
from pathlib import Path
import pymupdf  # PyMuPDF
import pytesseract
from PIL import Image

# Explicitly set the path to the Tesseract executable on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts raw text from a PDF file using PyMuPDF and Tesseract OCR."""
    full_text = ""
    try:
        doc = pymupdf.open(str(pdf_path))
        for page in doc:
            # First try native text extraction (faster)
            page_text = page.get_text()
            
            # Fall back to OCR if page contains no native text
            if not page_text.strip():
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img)
            
            full_text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path.name}: {e}")
    return full_text


def parse_drilling_events(text: str) -> dict:
    """Extracts attributes for historical_drilling_events table."""
    well_id = re.search(r'(?:Well\s*(?:ID|#)?[:\s]+)([A-Za-z0-9_\-]+)', text, re.IGNORECASE)
    lat = re.search(r'(?:Latitude|Lat)[:\s]+([-+]?\d*\.\d+|\d+)', text, re.IGNORECASE)
    lon = re.search(r'(?:Longitude|Long|Lon)[:\s]+([-+]?\d*\.\d+|\d+)', text, re.IGNORECASE)
    depth = re.search(r'(?:Event\s*Depth|Depth)[:\s]+(\d+(?:\.\d+)?)\s*(?:m|ft)?', text, re.IGNORECASE)
    event_type = re.search(r'(?:Event\s*Type|Event)[:\s]+([A-Za-z\s]+)', text, re.IGNORECASE)
    formation = re.search(r'(?:Formation)[:\s]+([A-Za-z0-9\s]+)', text, re.IGNORECASE)
    
    # Fixed regex patterns with escaped hyphen (\-)
    npt_duration = re.search(r'(?:NPT\s*Duration|NPT\s*Time)[:\s]+(\d+)\s*(?:min|mins|minutes)?', text, re.IGNORECASE)
    npt_category = re.search(r'(?:NPT\s*Category|NPT\s*Type)[:\s]+([A-Za-z0-9\s_\-]+)', text, re.IGNORECASE)

    return {
        "well_id": well_id.group(1).strip() if well_id else None,
        "latitude": float(lat.group(1)) if lat else None,
        "longitude": float(lon.group(1)) if lon else None,
        "event_depth": float(depth.group(1)) if depth else None,
        "event_type": event_type.group(1).strip() if event_type else None,
        "formation": formation.group(1).strip() if formation else None,
        "npt_duration_minutes": int(npt_duration.group(1)) if npt_duration else None,
        "npt_category": npt_category.group(1).strip() if npt_category else None,
        "summary_text": text[:500].replace('\n', ' ').strip()
    }


def parse_underground_infrastructure(text: str) -> dict:
    """Extracts attributes for underground_infrastructure table."""
    # Fixed regex patterns with escaped hyphen (\-)
    infra_id = re.search(r'(?:Infra\s*ID|Infrastructure\s*ID)[:\s]+([A-Za-z0-9_\-]+)', text, re.IGNORECASE)
    lat = re.search(r'(?:Infra\s*Lat|Latitude)[:\s]+([-+]?\d*\.\d+|\d+)', text, re.IGNORECASE)
    lon = re.search(r'(?:Infra\s*Long|Longitude)[:\s]+([-+]?\d*\.\d+|\d+)', text, re.IGNORECASE)
    depth = re.search(r'(?:Infra\s*Depth|Depth)[:\s]+(\d+(?:\.\d+)?)\s*(?:m|ft)?', text, re.IGNORECASE)
    
    infra_type = None
    type_match = re.search(r'(?:Infra\s*Type|Type)[:\s]+(Aquifer|Pipeline)', text, re.IGNORECASE)
    if type_match:
        infra_type = type_match.group(1).title()
    elif "aquifer" in text.lower():
        infra_type = "Aquifer"
    elif "pipeline" in text.lower():
        infra_type = "Pipeline"

    return {
        "infra_id": infra_id.group(1).strip() if infra_id else None,
        "latitude": float(lat.group(1)) if lat else None,
        "longitude": float(lon.group(1)) if lon else None,
        "depth_m": float(depth.group(1)) if depth else None,
        "infra_type": infra_type
    }

def process_all_reports():
    script_dir = Path(__file__).resolve().parent
    
    # Locate all .pdf files in the script directory
    pdf_files = list(script_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in directory: {script_dir}")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process.\n")

    for pdf_file in pdf_files:
        print(f"==================================================")
        print(f" Processing File: {pdf_file.name}")
        print(f"==================================================")
        
        # 1. Extract Text
        raw_text = extract_text_from_pdf(pdf_file)
        
        # 2. Extract Data via Rule-Based Logic
        event_data = parse_drilling_events(raw_text)
        infra_data = parse_underground_infrastructure(raw_text)

        # 3. Print Results
        print("\n--- Target Table: historical_drilling_events ---")
        for key, val in event_data.items():
            print(f"  {key}: {val}")

        print("\n--- Target Table: underground_infrastructure ---")
        for key, val in infra_data.items():
            print(f"  {key}: {val}")
        print("\n")


if __name__ == "__main__":
    process_all_reports()