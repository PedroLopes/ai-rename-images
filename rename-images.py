#!/usr/bin/env python3

# Credits
## This is a fork of https://raw.githubusercontent.com/Tedfulk/ollama-rename-img/refs/heads/main/ollama_rename_img/main.py

# Differences to original
## 1. Support for different models and custom prompts
##    1.1. You can specify the name of the model you want to use with your ollama: -m <name_of_model>
##    1.2. You can append extra information to the promp by adding: -p <your_extra_prompt>
##    1.3. Supports passing photo metadata to prompt by adding: -e TODO: might not be working properly
##    1.4. Supports resetting the conversation with AI model (by default, bypass with -k)

## 2. Dependencies
##    2.1. This version does not require the 'poetry' program to manage depedencies
##    2.2. Dependencies can be managed/install via the 'pip' program using the 'requirements.txt' file

## 3. Minor
##    3.1. File count disregards non jpeg/jpg files better
##
## TODO: check the parallelism

# User settings (e.g., alter the prompt, etc)

## Change prompt
##   Note that {number_of_words} will be replaced later with --number (-n) argument if supplied
original_prompt = ("Describe the image in {number_of_words} simple keywords, never use more than {number_of_words} words. ")

## Prompt format
##   Note that changing the prompt_output_format below is likely to cause errors (or requires code change)
prompt_output_format = ("Output in JSON format. "
                        "Use the following schema: { keywords: List[str] }.")

## Reset prompt
reset_prompt = "Reset conversation context."

# -------------
# built-in imports
# -------------
import argparse
import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import List

# -------------
# additional critical imports
# -------------
import ollama
from pydantic import BaseModel, Field
from tqdm import tqdm
#PIL is imported dynamically, neeed if you call with --exif (-e) to obtain image metadata

# -----------------------------
# Models
# -----------------------------

class ImageClassification(BaseModel):
    keywords: List[str] = Field(..., description="Keywords of the image.")

    def keywords_to_string_with_delimiter(self, delimiter: str = "_", number_of_words: int = 3) -> str:
        if delimiter not in ["_", "-", " "]: #this is late to do this check, weird
            raise ValueError("Delimiter must be underscore '_', dash '-', or space ' '")
        cleaned_keywords = [] 
        for keyword in self.keywords:
            if keyword.find(" "):
                new = keyword.replace(" ", "")
            cleaned_keywords.append(new)

        #cleaned_keywords = [
        #    keyword.replace(" ", delimiter)
        #    for keyword in self.keywords
        #    if not any(char.isdigit() for char in keyword) TODO: why can't have digit?
        #]
        return delimiter.join(cleaned_keywords[:number_of_words])

# -----------------------------
# Logging
# -----------------------------

logger = logging.getLogger(__name__)

def configure_logging(verbose: bool):
    logging.basicConfig(
        level=logging.INFO if verbose else logging.ERROR,
        format="%(levelname)s: %(message)s",
    )

# -----------------------------
# AI interaction
# -----------------------------

def generate_keywords(image_path: Path, extra_prompt: str, number_of_words: int, target_model: str, new_prompt: str, metadata: bool) -> dict:
    global original_prompt
    with image_path.open("rb") as img_file:
        base64_string = base64.b64encode(img_file.read()).decode("utf-8")
  
    # perform substitution of --number (-n) argument into {number_of_words}
    original_prompt = re.sub(r'{number_of_words}', str(number_of_words), original_prompt)

    if extra_prompt: 
        prompt = extra_prompt + " " + original_prompt #when --prompt (-p) is present, prepend a new prompt
    elif new_prompt:
        prompt = new_prompt #when --override (-o) is present, replace the entire prompt
    else: 
        prompt = original_prompt 

    if metadata: #only using PIL for exif info
        from PIL import Image
        with Image.open(image_path) as img:
            #print(image_path)
            exif_data = img.getexif()
            #print(exif_data)
            metadata_text = []
            for tag_id, value in exif_data.items():
                logger.info(f"{image_path}'s metadata:")
                tag_name = Image.TAGS.get(tag_id, tag_id) #this might not be working yet
                logger.info(f"\t{tag_name}: {value}")
                metadata_text.append(f"{tag_name}: {value};") 
            if metadata_text:
                prompt += "You might find clues in the image's metadata: " + str(metadata_text) + " "          
            else: 
                logger.info(f"{image_path}: metadata was empty")
 
    # add the format to the prompt
    prompt += prompt_output_format
    
    # Display the prompt to users
    logger.info(f"Using prompt: {prompt}")
 
    return ollama.chat(
        model=target_model,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [base64_string],
            }
        ],
    )

# -----------------------------
# Process images
# -----------------------------

def process_images(directory_path: Path, image_files: List[Path], delimiter: str, extra_prompt: str, number_of_words: int, target_model: str, new_prompt: str, metadata: bool):
    for file in tqdm(image_files, desc="Processing images", unit="image"):

        try:
            response = generate_keywords(file, extra_prompt, number_of_words, target_model, new_prompt, metadata)
            logger.info(f"Response: {response}")
            content = (
                response["message"]["content"]
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

            keywords = json.loads(content)
            image_classification = ImageClassification(**keywords)
            print(image_classification)

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
        "--override",
        "-o",
        type=str,
        help="Override the entire prompt (i.e., no other prompt but the text passed as argument)",
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="llava-phi3",
        help="Specify name of model that you want to use with ollama (default = llava-phi3)",
    )

    parser.add_argument(
        "--number",
        "-n",
        type=int,
        default=3,
        help="Specify the number of keywords to be generated when describing and image",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )

    parser.add_argument(
        "--exif",
        "-e",
        action="store_true",
        help="Enable parsing the metadata (EXIF) of a photo (e.g., author name, camera, GPS, etc) and pass this information to the prompt",
    )


    parser.add_argument(
        "--keep",
        "-k",
        action="store_true",
        default=False,
        help="Do not reset the AI-model's conversation (i.e., continues the previous session if ollama still has it running). By default this is always reset.",
    )

    args = parser.parse_args()
    configure_logging(args.verbose)

    if args.override and args.prompt:
        logger.error("ERROR: either use --override (-o) for a brand new prompt or --prompt (-p) to append to the default prompt, both simultaneously is nonsensical")
        return

    if not args.directory.exists():
        raise FileNotFoundError(f"Directory not found: {args.directory}")

    if not args.keep:
        logger.info("Requesting a reset of the conversation with AI mode.")
        ollama.chat(
            model=args.model,
            messages=[
                {
                    "role": "system",
                    "content": reset_prompt,
                }
            ],
        )

    image_files = []
    for file in args.directory.iterdir():
        if file.name.lower().endswith('.jpeg') or file.name.lower().endswith('.jpg'):
            image_files.append(Path(file))
        else: 
            continue

    if not image_files:
        logger.warning("No images to process (directory is likely empty of images).")
        return

    # process images
    process_images(args.directory, image_files, args.delimiter, args.prompt, args.number, args.model, args.override, args.exif)

# -----------------------------
# Program starts here, i.e., main call
# -----------------------------

if __name__ == "__main__":
    main()

