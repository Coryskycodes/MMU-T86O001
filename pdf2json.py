import re
import json
from datetime import datetime
from typing import List, Dict, Optional
from pypdf import PdfReader

#This part here for version
SCHEMA_VERSION = "1.0"

def create_law_schema(
    act_name: str,
    file_key: str,
    year: str,
    sections: List[Dict],
    last_updated: Optional[str] = None,
    version: str = "1.0",
    source: str = "Official gazette"
) -> Dict:
    if last_updated is None:
        last_updated = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "act_name": act_name,
            "file_key": file_key,
            "year": year,
            "last_updated": last_updated,
            "version": version,
            "total_sections": len(sections),
            "source": source
        },
        "sections": sections
    }

#get text
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:
            text += f"\n--- Page {page_number} ---\n{page_text}"
    return text

#section splitting
def split_into_sections(text: str, act_name: str) -> List[Dict]:
    pattern = r"(Section\s+\d+[A-Za-z]?\s*(?:\([^)]+\))?.*?)\n"
    parts = re.split(pattern, text)

    sections = []
    current = None

    for part in parts:
        if part.strip().startswith("Section"):
            if current:
                sections.append(current)

            match = re.match(r"Section\s+(\d+[A-Za-z]?)\s*(.*)", part.strip())
            current = {
                "act": act_name,
                "section": match.group(1) if match else "",
                "title": match.group(2).strip() if match else "",
                "text": ""
            }
        else:
            if current:
                current["text"] += part.strip() + " "

    if current:
        sections.append(current)
    if not sections:
        chunk_size = 1500
        for i in range(0, len(text), chunk_size):
            sections.append({
                "act": act_name,
                "section": f"Chunk {i//chunk_size + 1}",
                "title": "",
                "text": text[i:i+chunk_size]
            })

    return sections

#main
def pdf_to_json(
    pdf_path: str,
    json_output_path: str,
    act_name: str,
    file_key: str,
    year: str,
    last_updated: Optional[str] = None,
    source: str = "Official gazette"
):
    text = extract_text_from_pdf(pdf_path)
    sections = split_into_sections(text, act_name)
    law_json = create_law_schema(
        act_name=act_name,
        file_key=file_key,
        year=year,
        sections=sections,
        last_updated=last_updated,
        source=source
    )
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(law_json, f, ensure_ascii=False, indent=2)

    print(f"PDF successfully converted to JSON: {json_output_path}")
    print(f"Total sections found: {len(sections)}")


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# User portion
if __name__ == "__main__":
    pdf_path = "civil_law_act_1956.pdf"        #PDF file path example to use       r"C:/Users/PZY/Desktop/FYP/civil_law_act_1956.pdf
    json_output_path = "civil_law_act_1956.json"  #JSON output path
    act_name = "Civil Law Act 1956"
    file_key = "civil_law_act_1956"
    year = "1956"
    last_updated = "2026-01-17"
    source = "Migrated from legacy format"

    pdf_to_json(pdf_path, json_output_path, act_name, file_key, year, last_updated, source)
