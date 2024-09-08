import argparse
from time import perf_counter
from pathlib import Path
import re

from pdf_utils import extract_text_from_pdf, get_metadata
from ollama import call_ollama_api
from misc_utils import (
    is_valid_title,
    remove_empty_files,
    clear_screen,
    rename_pdf,
    sanitize_filename,
)


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
    response = call_ollama_api("llama3.1:latest", prompt)

    if isinstance(response, dict):
        response_text = response.get("response", "")
    elif isinstance(response, str):
        response_text = response
    else:
        print(f"\033[95mUnexpected response type: {type(response)}\033[0m")
        return "Title not found"

    match = re.search(r'"pdf_title":\s*"([^"]+)"', response_text)
    if match:
        return match.group(1)
    else:
        print("\033[95mTitle not found in LLM output\033[0m")
        return "Title not found"


def process_file(input_file, auto=False, force_llm=False) -> None:
    # leave a log for the auto flow, clear for the user one (it gets cluttered)
    if not auto:
        clear_screen()

    # Purple
    print(f"\033[95mProcessing: {input_file}\033[0m")
    new_title = None

    text = extract_text_from_pdf(input_file)
    if not text:
        return

    if force_llm:
        t1 = perf_counter()
        new_title = generate_title_with_llm(text)
        end = perf_counter() - t1

        # Green to match reccomendation in upcoming choices
        print(f"\033[92mGenerated title: {new_title} in {end}s\033[0m")

        rename_pdf(input_file, sanitize_filename(new_title), auto)
        return

    metadata = get_metadata(input_file)
    metadata_title = metadata.get("title", None)
    if metadata_title and is_valid_title(metadata_title):
        print(f"Using metadata title: {metadata_title}")
        new_title = sanitize_filename(metadata_title)
        rename_pdf(input_file, new_title, auto)
    else:
        print(f"Forcing LLM to generate a title")
        process_file(input_file, auto=auto, force_llm=True)
        print("\033[95mFallback to using LLM to generate a title...\033[0m")


def main():
    parser = argparse.ArgumentParser(
        description="Process PDF files and rename based on content."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input PDF file or directory containing PDFs",
    )
    parser.add_argument(
        "--auto",
        type=bool,
        required=False,
        help="Let the llm/title found write the filenames automatically without user prompting [not a good idea?]",
    )
    parser.add_argument(
        "--force-llm",
        type=bool,
        required=False,
        default=False,
        help="Force the llm to be used, skipping metadata even if available",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.is_dir():
        for file in input_path.glob("*.pdf"):
            remove_empty_files(file)
            process_file(file, args.auto, args.force_llm)
    else:
        process_file(input_path, args.auto, args.force_llm)


if __name__ == "__main__":
    main()
