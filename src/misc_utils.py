import os
import shutil
import re
from pathlib import Path


def backup_and_rename(original_path: str, new_title: str) -> Path:
    """
    Gives you back the newly created Path if successful.
    Note: by default it will place 'backups' in the directory you're running from.
    """
    directory, filename = os.path.split(original_path)
    new_filename = new_title.replace(" ", "_") + ".pdf"
    backup_path = os.path.join(directory, "backup", filename)
    new_path = os.path.join(directory, new_filename)

    os.makedirs(os.path.join(directory, "backup"), exist_ok=True)
    shutil.copy2(original_path, backup_path)
    os.rename(original_path, new_path)

    return Path(new_path)


def sanitize_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|,]', "", title)


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def is_valid_title(title) -> bool:
    # Check if the title contains at least one alphanumeric character
    return bool(re.search(r"[a-zA-Z0-9]", title)) and not all(c == "?" for c in title)


def rename_pdf(input_path, new_title, auto=False) -> None:
    input_path = Path(input_path)
    directory = input_path.parent
    processed_dir = directory / "processed"
    processed_dir.mkdir(exist_ok=True)

    new_title_sanitized = sanitize_filename(new_title)
    if len(new_title_sanitized) > 128:
        print(
            f"Suggested filename {new_title_sanitized}, is too darn long! truncating!!!"
        )
        new_title_sanitized = new_title_sanitized[:128]
    new_file_name = f"{new_title_sanitized}.pdf"
    new_path = processed_dir / new_file_name

    print(f"\033[33mOld File Name:\033[0m {input_path.name}")
    print(f"\033[32mNew File Name:\033[0m {new_file_name}")

    if auto:
        input_path.rename(new_path)
        return

    response = input("Rename? (y/n/something random): ")
    if response.lower() == "y":
        input_path.rename(new_path)
        print(f"File renamed to: {new_path}")
    elif response.lower() == "n":
        print("No changes made.")
        return
    else:
        response.strip(".pdf")  # we're gonna add it so just incase they already have.
        custom_path = processed_dir / f"{sanitize_filename(response)}.pdf"
        input_path.rename(custom_path)
        print(f"File renamed to: {custom_path}")


def remove_empty_files(file: Path):
    """Removes all files of size 0 bytes."""
    if file.is_file() and file.stat().st_size == 0:
        # red
        print(f"\033[31mRemoving empty file:\033[0m {file}")
        file.unlink()
