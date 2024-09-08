import os
import argparse


def strip_keyword_from_files(root_dir, keyword, dry_run=False):
    print(f"Looking in: {root_dir} for files containing: '{keyword}'")
    found = False
    for path, _, files in os.walk(root_dir):
        for file in files:
            print(f"Checking file: {file}")
            if keyword in file:
                found = True
                new_name = file.replace(keyword, "")
                print(f"Matched keyword in file: {file}")
                if not dry_run:
                    os.rename(os.path.join(path, file), os.path.join(path, new_name))
                else:
                    print(f"old: {file} -> new: {new_name}")
    if not found:
        print("No files found containing the keyword.")


def main():
    parser = argparse.ArgumentParser(
        description="Strip a specified keyword from file names."
    )

    parser.add_argument(
        "--input", type=str, required=True, help="A directory, cannot be a single file."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the action without making any changes.",
    )
    parser.add_argument("keyword", type=str, help="Keyword to remove from file names.")

    args = parser.parse_args()

    strip_keyword_from_files(args.input, args.keyword, args.dry_run)


if __name__ == "__main__":
    main()
