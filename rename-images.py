#!/usr/bin/env python3

# Credits
## This is a fork of https://raw.githubusercontent.com/Tedfulk/ollama-rename-img/refs/heads/main/ollama_rename_img/main.py

# Differences to original
## 1. dependencies
##    1.1. this does not require poetry to manage depedencies
##    1.2. dependencies can be managed with pip via requirements.txt



import argparse
import base64
import json
import logging
import os
from pathlib import Path
from typing import List

import ollama
from PIL import Image
from pydantic import BaseModel, Field
from tqdm import tqdm


# -----------------------------
# Models
# -----------------------------

class ImageClassification(BaseModel):
    keywords: List[str] = Field(..., description="Keywords of the image.")

    def keywords_to_string_with_delimiter(self, delimiter: str = "_") -> str:
        if delimiter not in ["_", "-", " "]:
            raise ValueError("Delimiter must be underscore '_', dash '-', or space ' '")

        cleaned_keywords = [
            keyword.replace(" ", delimiter)
            for keyword in self.keywords
            if not any(char.isdigit() for char in keyword)
        ]
        return delimiter.join(cleaned_keywords[:5])


# -----------------------------
# Logging
# -----------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def configure_logging(verbose: bool):
    logging.basicConfig(
        level=logging.INFO if verbose else logging.ERROR,
        format="%(levelname)s: %(message)s",
    )


# -----------------------------
# Image helpers
# -----------------------------

def convert_webp_to_jpeg(file_path: str) -> str:
    if not file_path.lower().endswith(".webp"):
        return ""

    try:
        with Image.open(file_path) as img:
            new_file_path = os.path.splitext(file_path)[0] + ".jpeg"
            img.convert("RGB").save(new_file_path, "JPEG")
            return new_file_path
    except IOError:
        logger.error(f"Failed to convert {file_path}")
        return ""


def convert_files_to_jpeg(directory_path: Path) -> List[Path]:
    converted = []
    for file in directory_path.iterdir():
        #if file.is_file() and file.suffix.lower() == ".webp":
        #    jpeg_path = convert_webp_to_jpeg(str(file))
        #    if jpeg_path:
        #        converted.append(Path(jpeg_path))
        converted.append(Path(file))
    return converted


# -----------------------------
# AI interaction
# -----------------------------

def generate_keywords(image_path: Path) -> dict:
    with image_path.open("rb") as img_file:
        base64_string = base64.b64encode(img_file.read()).decode("utf-8")
        

    return ollama.chat(
        model="llava-phi3",
        messages=[
            {
                "role": "user",
                "content": (
                    "Describe the image in 4 simple keywords. "
                    "Output in JSON format. "
                    "Use the following schema: { keywords: List[str] }."
                ),
                "images": [base64_string],
            }
        ],
    )


# -----------------------------
# Core processing
# -----------------------------

def process_images(
    directory_path: Path,
    converted_files: List[Path],
    webp_files: List[Path],
    delimiter: str,

):
    for file in tqdm(converted_files, desc="Processing images", unit="image"):
    #for file in converted_files:
        if file.name == ".DS_Store":
            continue

        try:
            response = generate_keywords(file)
            content = (
                response["message"]["content"]
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            keywords = json.loads(content)
            image_classification = ImageClassification(**keywords)

            new_name = image_classification.keywords_to_string_with_delimiter(delimiter)
            new_path = directory_path / f"{new_name}{file.suffix}"

            file.rename(new_path)
            logger.info(f"Renamed {file.name} → {new_path.name}")
            print(f"Renamed {file.name} → {new_path.name}")

            #webp_file = next((w for w in webp_files if w.stem == file.stem), None)
            #if webp_file:
            #    webp_file.unlink()
            #    webp_files.remove(webp_file)

        except Exception as e:
            logger.error(f"Error processing {file}: {e}")

    #for remaining in webp_files:
    #    logger.warning(f"Unprocessed WebP file: {remaining}")


# -----------------------------
# CLI
# -----------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Rename image files based on their content using AI-generated keywords."
    )

    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing the images",
    )

    parser.add_argument(
        "--delimiter",
        "-d",
        default="_",
        choices=["_", "-", " "],
        help="Delimiter for keywords in filename (default: _)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()
    configure_logging(args.verbose)

    if not args.directory.exists():
        raise FileNotFoundError(f"Directory not found: {args.directory}")

    #webp_files = list(args.directory.glob("*.webp"))
    webp_files = []
    converted = convert_files_to_jpeg(args.directory)

    if not converted:
        logger.warning("No images to process.")
        return

    process_images(args.directory, converted, webp_files, args.delimiter)


# -----------------------------
# Entry point
# -----------------------------

if __name__ == "__main__":
    main()

