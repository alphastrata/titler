import os
import shutil
import re


def backup_and_rename(original_path, new_title):
    directory, filename = os.path.split(original_path)
    new_filename = new_title.replace(" ", "_") + ".pdf"
    backup_path = os.path.join(directory, "backup", filename)
    new_path = os.path.join(directory, new_filename)

    # Ensure backup directory exists
    os.makedirs(os.path.join(directory, "backup"), exist_ok=True)
    # Create backup
    shutil.copy2(original_path, backup_path)
    # Rename original to new title
    os.rename(original_path, new_path)


def sanitize_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|,]', "", title)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def is_valid_title(title):
    # Check if the title contains at least one alphanumeric character
    return bool(re.search(r"[a-zA-Z0-9]", title)) and not all(c == "?" for c in title)
