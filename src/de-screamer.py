import argparse
from pathlib import Path
import re
import os
from PyPDF2 import PdfReader, PdfWriter


def set_pdf_title(pdf_path: Path, new_title: str):
    try:
        reader = PdfReader(str(pdf_path))
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)

        # New way to set metadata using PyPDF2
        metadata = {"/Title": new_title}
        writer.add_metadata(metadata)

        new_pdf_path = pdf_path.with_suffix(".pdf_temp")
        with new_pdf_path.open("wb") as f_out:
            writer.write(f_out)
        new_pdf_path.replace(pdf_path)
    except Exception as e:
        print(f"\033[91mError processing {pdf_path}: {e}\033[0m")  # Print error in red


def sanitise_title(s: str) -> str:
    s = re.sub(r"[{}[\]()*]", "", s)  # Remove special characters
    s = re.sub(r"\.\.+$", ".", s)  # Replace multiple trailing periods with a single one
    s = s.strip()  # Trim whitespace from the ends
    return s


def rename_and_set_title(p: Path, dry_run: bool = False):
    file_title = sanitise_title(p.stem)
    new_title = " ".join(
        word.capitalize()
        if word.lower() not in ["of", "and", "in", "on", "at", "to"]
        else word.lower()
        for word in file_title.split()
    )
    new_file_name = f"{new_title}.pdf"
    new_file_path = p.parent / new_file_name

    if dry_run:
        print(f"\033[93mOld: {p}\033[0m")  # Yellow
        print(f"\033[96mNew: {new_file_path}\033[0m")  # Cyan
    else:
        try:
            os.rename(p, new_file_path)
            set_pdf_title(new_file_path, new_title)
            print(f"Renamed and updated metadata for: {new_file_name}")
        except Exception as e:
            print(f"\033[91mError processing {p}: {e}\033[0m")  # Print error in red


def run(paths, dry_run):
    for p in paths:
        rename_and_set_title(p, dry_run)


def main():
    parser = argparse.ArgumentParser(
        description="Rename PDF files and update their title metadata."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input directory or file pattern for PDF files.",
    )
    parser.add_argument(
        "--extension",
        type=str,
        default="pdf",
        help='File extension to filter by, default is "pdf".',
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the changes without making them."
    )
    args = parser.parse_args()

    try:
        # Ensure input is a directory or valid path
        input_path = Path(args.input)
        if input_path.is_dir():
            # Recursively find files with the given extension
            pdf_files = list(input_path.rglob(f"*.{args.extension}"))
        else:
            # Handle the case where a specific file or pattern is given
            pdf_files = list(input_path.parent.glob(input_path.name))

        # Run the renaming process
        run(pdf_files, args.dry_run)
    except Exception as e:
        print(
            f"\033[91mAn error occurred while setting up the process: {e}\033[0m"
        )  # General setup error in red


if __name__ == "__main__":
    main()
