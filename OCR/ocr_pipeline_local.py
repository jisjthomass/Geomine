import os
import re
from pathlib import Path
import pymupdf
import pytesseract
from PIL import Image

if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path: Path) -> str:
    full_text = ""
    try:
        doc = pymupdf.open(str(pdf_path))
        for page in doc:
            page_text = page.get_text()
            if not page_text.strip():
                pix = page.get_pixmap(dpi=150)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img)
            full_text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path.name}: {e}")
    return full_text

def parse_drilling_events(text: str) -> dict:
    clean_text = re.sub(r'\s+', ' ', text)
    
    well_id = re.search(r'Well\s*(?:ID|No|#)?\s*[:\-]?\s*([A-Za-z0-9_\-]+)', clean_text, re.IGNORECASE)
    lat = re.search(r'Lat(?:itude)?\s*[:\-]?\s*([-+]?\d*\.\d+|\d+)', clean_text, re.IGNORECASE)
    lon = re.search(r'Lon(?:gitude|g)?\s*[:\-]?\s*([-+]?\d*\.\d+|\d+)', clean_text, re.IGNORECASE)
    depth = re.search(r'Depth\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:m|ft|meters)', clean_text, re.IGNORECASE)
    
    npt_duration = re.search(r'NPT\s*(?:Duration|Time)\s*[:\-]?\s*(\d+)\s*(?:min|hrs|hours)', clean_text, re.IGNORECASE)
    npt_category = re.search(r'NPT\s*(?:Category|Type)\s*[:\-]?\s*([A-Za-z0-9\s_\-]+?)(?=\s*(?:NPT|$))', clean_text, re.IGNORECASE)

    return {
        "well_id": well_id.group(1).strip() if well_id else None,
        "latitude": float(lat.group(1)) if lat else None,
        "longitude": float(lon.group(1)) if lon else None,
        "event_depth": float(depth.group(1)) if depth else None,
        "npt_duration_minutes": int(npt_duration.group(1)) if npt_duration else None,
        "npt_category": npt_category.group(1).strip() if npt_category else None,
        "summary_text": clean_text[:500].strip()
    }

def parse_underground_infrastructure(text: str) -> dict:
    clean_text = re.sub(r'\s+', ' ', text)
    
    infra_id = re.search(r'(?:Infra|Infrastructure)\s*ID\s*[:\-]?\s*([A-Za-z0-9_\-]+)', clean_text, re.IGNORECASE)
    lat = re.search(r'(?:Infra|Infrastructure)\s*Lat(?:itude)?\s*[:\-]?\s*([-+]?\d*\.\d+|\d+)', clean_text, re.IGNORECASE)
    lon = re.search(r'(?:Infra|Infrastructure)\s*Lon(?:gitude|g)?\s*[:\-]?\s*([-+]?\d*\.\d+|\d+)', clean_text, re.IGNORECASE)
    depth = re.search(r'(?:Infra|Infrastructure)\s*Depth\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:m|ft)', clean_text, re.IGNORECASE)
    
    infra_type = None
    if "aquifer" in clean_text.lower():
        infra_type = "Aquifer"
    elif "pipeline" in clean_text.lower():
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
    pdf_files = list(script_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in directory: {script_dir}")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process.\n")

    for pdf_file in pdf_files:
        print(f"==================================================")
        print(f" Processing File: {pdf_file.name}")
        print(f"==================================================")
        
        raw_text = extract_text_from_pdf(pdf_file)
        
        event_data = parse_drilling_events(raw_text)
        infra_data = parse_underground_infrastructure(raw_text)

        print("\n--- Target Table: historical_drilling_events ---")
        for key, val in event_data.items():
            print(f"  {key}: {val}")

        print("\n--- Target Table: underground_infrastructure ---")
        for key, val in infra_data.items():
            print(f"  {key}: {val}")
        print("\n")

if __name__ == "__main__":
    process_all_reports()
