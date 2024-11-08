import fire
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from time import perf_counter
import re
import os
import sys
import fitz  # PyMuPDF, for PDF handling
import json
import requests
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Capture all levels; handlers will filter

# Handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('error.log')

# Set default levels (adjusted in main())
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.ERROR)

# Formatters
console_formatter = logging.Formatter('%(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

console_handler.setFormatter(console_formatter)
file_handler.setFormatter(file_formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return None

# Function to get metadata from PDF
def get_metadata(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata
        doc.close()
        return metadata
    except Exception as e:
        logger.error(f"Error getting metadata from {pdf_path}: {e}")
        return {}

# Function to call the LLM API (replace with actual API details)
def call_ollama_api(model_name, prompt):
    # Replace with actual API call code
    url = f"http://localhost:11434/generate"
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": model_name,
        "prompt": prompt
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '')
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return ""

# Utility functions
def is_valid_title(title):
    return title and len(title.strip()) > 5

def remove_empty_files(file_path):
    if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
        os.remove(file_path)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def rename_pdf(input_file, new_title, auto=False, output_dir=None):
    new_file_name = f"{new_title}.pdf"
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        new_file_path = output_dir / new_file_name
    else:
        new_file_path = input_file.parent / new_file_name

    if new_file_path.exists():
        logger.info(f"File {new_file_name} already exists.")
        return
    if auto:
        input_file.rename(new_file_path)
        logger.info(f"Renamed to {new_file_name}")
    else:
        response = input(f"Rename '{input_file.name}' to '{new_file_name}'? [y/N]: ")
        if response.lower() == 'y':
            input_file.rename(new_file_path)
            logger.info(f"Renamed to {new_file_name}")
        else:
            logger.info("Rename cancelled.")

def generate_title_with_llm(text):
    prompt = f"""
### Template:
{{
    "pdf_title": "",
    "pdf_journal":"",
    "pdf_volume_issue":"",
    "pdf_url":"",
    "pdf_authors":""
    
}}
### Example:
"Filtering After Shading With Stochastic Texture Filtering
MATT PHARR∗, NVIDIA, USA
BARTLOMIEJ WRONSKI∗, NVIDIA, USA
MARCO SALVI, NVIDIA, USA
MARCOS FAJARDO, Shiokara–Engawa Research, Spain
2D texture maps and 3D voxel arrays are widely used to add rich detail to the surfaces and volumes of
rendered scenes, and filtered texture lookups are integral to producing high-quality imagery. We show that
applying the texture filter after evaluating shading generally gives more accurate imagery than filtering
textures before BSDF evaluation, as is current practice. These benefits are not merely theoretical, but are
apparent in common cases. We demonstrate that practical and efficient filtering after shading is possible
through the use of stochastic sampling of texture filters.
Stochastic texture filtering offers additional benefits, including efficient implementation of high-quality
texture filters and efficient filtering of textures stored in compressed and sparse data structures, including
neural representations. We demonstrate applications in both real-time and offline rendering and show that
the additional error from stochastic filtering is minimal. We find that this error is handled well by either
spatiotemporal denoising or moderate pixel sampling rates.
CCS Concepts: • Computing methodologies → Texturing; Antialiasing; Ray tracing; Rasterization.
ACM Reference Format:
Matt Pharr, Bartlomiej Wronski, Marco Salvi, and Marcos Fajardo. 2024. Filtering After Shading With Stochastic
Texture Filtering. Proc. ACM Comput. Graph. Interact. Tech. 7, 1, Article 1 (May 2024), 29 pages. https://doi.org/
10.1145/3651293
1 INTRODUCTION
Image texture maps play a crucial role in achieving rich surface detail in most rendered images.
The availability of advanced texture painting tools provides artists with precise and natural control
over the material appearance. Three-dimensional voxel grids play a similar role for volumetric
effects like clouds, smoke, and fire, allowing detailed offline physical simulations to be used. The
number and resolution of both has continued to increase over the years.
Typical practice in rendering is to perform filtered texture lookups to find the values of shading
parameters. We demonstrate that filtering before shading introduces error if those parameters
make a nonlinear contribution to the final result. We show that applying the texture filter after
shading instead gives a more accurate result in these cases. However, a naive implementation of
filtering after shading imposes an increased computational cost. A family of efficient stochastic
texture filtering algorithms allows to efficiently filter after shading, potentially with only a single
texel access for each texture map lookup (Figure 1)."
{{'pdf_contents": {text} ',\n "pdf_title": "Filtering After Shading With Stochastic Texture Filtering",
}}
### Text:
{{'pdf_contents": {text} ',\n"pdf_title": ""}}
"""

    response = call_ollama_api("gemma2:2b", prompt)

    
    if isinstance(response, dict):
        response_text = response.get("response", "")
    elif isinstance(response, str):
        response_text = response
    else:
        logger.error(f"Unexpected response type: {type(response)}")
        return "Title not found"

    match = re.search(r'"pdf_title":\s*"([^"]+)"', response_text)
    if match:
        return match.group(1)
    else:
        logger.error("Title not found in LLM output")
        return "Title not found"

def process_file(input_file, auto=False, force_llm=False, output_dir=None):
    try:
        logger.info(f"\033[95mProcessing: {input_file}\033[0m")
        new_title = None

        text = extract_text_from_pdf(input_file)
        if not text:
            return

        if force_llm:
            t1 = perf_counter()
            new_title = generate_title_with_llm(text)
            end = perf_counter() - t1

            logger.info(f"\033[92mGenerated title: {new_title} in {end:.2f}s\033[0m")

            rename_pdf(input_file, sanitize_filename(new_title), auto, output_dir)
            return

        metadata = get_metadata(input_file)
        metadata_title = metadata.get("title", None)
        if metadata_title and is_valid_title(metadata_title):
            logger.info(f"Using metadata title: {metadata_title}")
            new_title = sanitize_filename(metadata_title)
            rename_pdf(input_file, new_title, auto, output_dir)
        else:
            logger.info("Forcing LLM to generate a title")
            t1 = perf_counter()
            new_title = generate_title_with_llm(text)
            end = perf_counter() - t1

            logger.info(f"\033[92mGenerated title: {new_title} in {end:.2f}s\033[0m")

            rename_pdf(input_file, sanitize_filename(new_title), auto, output_dir)

    except Exception as e:
        logger.error(f"Error processing {input_file}: {e}")

def process_files_concurrently(files, auto=False, force_llm=False, output_dir=None):
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(process_file, file, auto, force_llm, output_dir): file
            for file in files
        }
        # Always show the progress bar
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing PDFs", disable=False):
            try:
                future.result()
            except Exception as e:
                file = futures[future]
                logger.error(f"Error processing {file}: {e}")

def main(input, auto=False, force_llm=False, silent=False, output_dir=None):
    # Adjust logging level based on silent flag
    if silent:
        console_handler.setLevel(logging.CRITICAL)
    else:
        console_handler.setLevel(logging.INFO)

    input_path = Path(input)
    if input_path.is_dir():
        files = list(input_path.glob("*.pdf"))
        for file in files:
            remove_empty_files(file)
        process_files_concurrently(files, auto, force_llm, output_dir)
    else:
        remove_empty_files(input_path)
        process_file(input_path, auto, force_llm, output_dir)

if __name__ == "__main__":
    fire.Fire(main)
