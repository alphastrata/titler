import os
import torch
import argparse
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
import re
import shutil
import datetime

from misc_utils import rename_pdf
from pdf_utils import extract_text_from_pdf

print(torch.__version__)

LLMOUTPUT = ""
EXAMPLE = json.dumps(
    {
        "pdf_title": "Simple Analytic Approximations to the CIE XYZ Color Matching Functions",
        "pdf_contents": "Journal of Computer Graphics Techniques\nSimple Analytic Approximations to the CIE XYZ Color Matching Functions\nVol. 2, No. 2, 2013\nhttp://jcgt.org\nSimple Analytic Approximations to the CIE XYZ\nColor Matching Functions\nChris Wyman Peter-Pike Sloan\nNVIDIA\nPeter Shirley\nAbstract\nWe provide three analytical fits to the CIE ¯x, ¯y, and ¯z color matching curves commonly used in predictive and spectral renderers as an intermediate between light spectra and RGB col- ors...",
        "pdf_title": "Simple Analytic Approximations to the CIE XYZ Color Matching Functions",
        "pdf_journal": "Journal of Computer Graphics Techniques",
        "pdf_volume_issue": "Vol. 2, No. 2, 2013",
        "pdf_url": "http://jcgt.org",
        "pdf_authors": "Chris Wyman, Peter-Pike Sloan, NVIDIA, Peter Shirley",
    },
    indent=4,
)


def log_time(message: str):
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    print(f"[{timestamp}][INFO] {message}")


def predict_title_from_pdf(model, tokenizer, text: str) -> str:
    global LLMOUTPUT

    start_time = datetime.datetime.now()
    schema = json.dumps({"pdf_title": "", "pdf_contents": f"{text}"}, indent=4)
    input_llm = (
        "\n### Template:\n"
        + schema
        + "\n### Example:\n"
        + EXAMPLE
        + "\n### Text:\n"
        + text
        + "\n\n"
    )
    input_ids = tokenizer(
        input_llm, return_tensors="pt", truncation=True, max_length=1024
    ).to("cuda")
    output = model.generate(**input_ids)[0]
    decoded_output = tokenizer.decode(output, skip_special_tokens=True)
    last_llm_output = decoded_output.replace(EXAMPLE, "")
    LLMOUTPUT = last_llm_output
    end_time = datetime.datetime.now()
    log_time(f"predict_title_from_pdf duration: {end_time - start_time}")
    return last_llm_output.split("<|end-output|>")[0]


def run(model, tokenizer, text: str) -> str:
    title = predict_title_from_pdf(model, tokenizer, text)
    return title


def sanitize_filename(title: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", title)


def pull_title_from_raw(raw: str) -> str:
    lines = raw.split("\n")
    start_capture = False
    json_data_str = ""
    for line in lines:
        if "### Response:" in line:
            start_capture = True
        elif start_capture:
            json_data_str += line
            if line.strip() == "}":
                break
    if json_data_str:
        try:
            json_data = json.loads(json_data_str)
            return json_data.get("pdf_title", "Title not found")
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return "Title not found"
    else:
        print("No JSON data found in response")
        return "Title not found"


def process_file(model, tokenizer, input_file):
    try:
        text = extract_text_from_pdf(input_file)
        if text:
            title_raw = run(model, tokenizer, text)
            new_title = pull_title_from_raw(title_raw)
            print(f"captured: {new_title}")
            rename_pdf(input_file, new_title)
    except:
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract text from PDF and query Ollama API."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input PDF file or directory containing PDFs",
    )
    args = parser.parse_args()
    model = AutoModelForCausalLM.from_pretrained(
        "numind/NuExtract", torch_dtype=torch.bfloat16, trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(
        "numind/NuExtract", trust_remote_code=True
    )
    model.to("cuda")
    model.eval()

    if os.path.isdir(args.input):
        for filename in os.listdir(args.input):
            if filename.endswith(".pdf"):
                process_file(model, tokenizer, os.path.join(args.input, filename))
    else:
        process_file(model, tokenizer, args.input)
