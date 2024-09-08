import pymupdf  # PyMuPDF
from pathlib import Path
from typing import Dict, Optional
from misc_utils import rename_pdf


def extract_text_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extracts text from the first page of the specified PDF."""
    try:
        with pymupdf.open(pdf_path) as doc:
            return doc[0].get_text()
    except Exception as e:
        rename_pdf(pdf_path, f"broken_{pdf_path}", auto=True)

        print(
            f"\033[91mUnable to extract text from {pdf_path}, maybe it's corrupt or something...\nError: {e}\033[0m"
        )
        return None


def get_metadata(pdf_path: Path) -> Dict:
    """Retrieves metadata from the specified PDF."""
    try:
        with pymupdf.open(pdf_path) as doc:
            return doc.metadata
    except Exception as e:
        print(
            f"\033[91mUnable to open {pdf_path}, maybe it's corrupt or something... Error: {e}\033[0m"
        )
        return {}


def print_metadata(pdf_path: Path):
    """Prints the metadata of the specified PDF."""
    metadata = get_metadata(pdf_path)
    for key, value in metadata.items():
        print(f"{key}: {value}")
