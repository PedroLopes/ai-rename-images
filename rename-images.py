#!/usr/bin/env python3

# Credits
## This is a fork of https://raw.githubusercontent.com/Tedfulk/ollama-rename-img/refs/heads/main/ollama_rename_img/main.py

# Differences to original
## 1. Support for custom prompts
##    1.1. 

## 2. Dependencies
##    2.1. This version does not require the 'poetry' program to manage depedencies
##    2.2. Dependencies can be managed/install via the 'pip' program using the 'requirements.txt' file
##
##


## format: words sepetrated by spaces, are collapsed into cinamon bun cinamonBun

# user settings (e.g., alter the prompt, etc)
original_prompt = ("Describe the image in {number_of_words} simple keywords, never use more than {number_of_words} words. "
                  "Output in JSON format. "
                  "Use the following schema: { keywords: List[str] }.")

#original_prompt = ("Ignore any previous request to describe images. Just respond with the word test. Use the following schema: { keywords: List[str] }.")

# built-in imports
import argparse
import base64
import json
import logging
import os
from pathlib import Path
from typing import List

# additional critical imports
import ollama
from PIL import Image
from pydantic import BaseModel, Field
from tqdm import tqdm

# -----------------------------
# Models
# -----------------------------

class ImageClassification(BaseModel):
    keywords: List[str] = Field(..., description="Keywords of the image.")

    def keywords_to_string_with_delimiter(self, delimiter: str = "_", number_of_words: int = 3) -> str:
        if delimiter not in ["_", "-", " "]: #this is late to do this check, weird
            raise ValueError("Delimiter must be underscore '_', dash '-', or space ' '")

        cleaned_keywords = []
        # i want to this in a stabdard for loop
        #for keyword in self.keywords: #add a number iter, so we can exit if
        #    if iter > number_of_words:
        #        break
            # pass #keep adding
        #    keyword.replace(" ", delimiter)
        print("N: " + str(number_of_words))
       
        cleaned_keywords = [
            keyword.replace(" ", delimiter)
            for keyword in self.keywords
            if not any(char.isdigit() for char in keyword)
        ]
        return delimiter.join(cleaned_keywords[:number_of_words])


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

def convert_files_to_jpeg(directory_path: Path) -> List[Path]:
    return converted


# -----------------------------
# AI interaction
# -----------------------------

def generate_keywords(image_path: Path, extra_prompt: str, number_of_words: int) -> dict:
    with image_path.open("rb") as img_file:
        base64_string = base64.b64encode(img_file.read()).decode("utf-8")
    logger.info(f"{extra_prompt}")
    
    original_prompt = f("Describe the image in {number_of_words} simple keywords, never use more than {number_of_words} words. "
                  "Output in JSON format. "
                  "Use the following schema: { keywords: List[str] }.")


    prompt = original_prompt #needs to rehash it here with f{}
    if extra_prompt:
        prompt = extra_prompt + original_prompt
    print(prompt)
 
    return ollama.chat(
        model="llava-phi3",
        messages=[
            {
                "role": "user",
                #"content": (
                #    "Describe the image in 4 simple keywords. "
                #    "Output in JSON format. "
                #    "Use the following schema: { keywords: List[str] }."
                #),
                "content": prompt,
                "images": [base64_string],
            }
        ],
    )


# -----------------------------
# Core processing
# -----------------------------

def process_images(directory_path: Path, converted_files: List[Path], delimiter: str, extra_prompt: str, number_of_words: int):
    for file in tqdm(converted_files, desc="Processing images", unit="image"):
        if file.name == ".DS_Store": #mac only to skip system files, probably best to change to ".*" regex
            continue

        try:
            response = generate_keywords(file, extra_prompt, number_of_words)
            print(response)
            content = (
                response["message"]["content"]
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            keywords = json.loads(content)
            image_classification = ImageClassification(**keywords)

            new_name = image_classification.keywords_to_string_with_delimiter(delimiter, number_of_words)
            new_path = directory_path / f"{new_name}{file.suffix}"

            file.rename(new_path)
            logger.info(f"Renamed {file.name} → {new_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file}: {e}")


# -----------------------------
# CLI arguments
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
        "--prompt",
        "-p",
        type=str,
        help="Add extra requests to the existing prompt (see code for existing prompt)",
    )

    parser.add_argument(
        "--number",
        "-n",
        type=int,
        default=3,
        help="TODO",
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

    converted = []
    for file in args.directory.iterdir():
        converted.append(Path(file))

    if not converted:
        logger.warning("No images to process (directory is likely empty of images).")
        return

    # process images
    process_images(args.directory, converted, args.delimiter, args.prompt, args.number)

# -----------------------------
# Program starts here, i.e., main call
# -----------------------------

if __name__ == "__main__":
    main()

