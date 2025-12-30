# AI Image Renamer (Ollama-based)

Rename JPEG images automatically using AI-generated keywords derived from image content (and optionally metadata). It uses **Ollama multimodal models** to analyze images and generate concise, human-readable filenames. This can use local models, you control which model to use via ollama.

This project is a **fork and extension** of [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img).

---

## Features

- Rename `.jpg` / `.jpeg` images based on visual content (same as [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img))
- Supports **any Ollama vision-capable model** (unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).
- Customizable prompts (append or fully override, unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).
- Optional conversation persistence with the model (unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).
- Optional EXIF metadata injection into the prompt (unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).
- Optional GPS reverse-geocoding (via `exiftool`) (unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).
-  No Poetry dependency — plain `pip` + `requirements.txt` (unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).
- Allows custom prefix/postfix, allows parsing timestamps, and more (unlike [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img)).

---

## How It Works

For each image, the program:

1. Opens the image (optionally extracts metadata, GPS location, etc)
2. Sends it to an Ollama vision model with a structured prompt (including custom prompts via command line)
3. Expects a JSON response with keywords (optionally, you can set how many of these you want)
4. Converts keywords into a filename
5. Renames the image in-place

---

## Install and requirements

### What you need
- Python **3.9+**
- [Ollama](https://ollama.com/) running locally
- A vision-capable Ollama model (e.g. `llava-phi3`)

### Installation

Clone the repository and make the installer executable and install it:

```bash
git clone https://github.com/PedroLopes/ai-rename-images
cd ai-rename-images
chmod +x install.sh
./install.sh
```

Alternatively, if you want to do it manually:

```bash
git clone https://github.com/PedroLopes/ai-rename-images
cd ai-rename-images
pip install -r requirements.txt
chmod +x ai_rename_images.py 
```
Now you can invoke it using:

```bash
./ai-rename-images <directory-with-images>
```

Or you can keep invoking it explicitly with ``python3`` (without ``chmod +x`` to create an executable).

```bash
python3 ai_rename_images.py <directory-with-images>
```

## Command-Line Options

### Core Options

| Option | Description |
|------|-------------|
| `directory` | Directory containing images |
| `-m, --model` | Ollama model to use (default: `llava-phi3`) |
| `-n, --number` | Number of keywords (default: `3`) |
| `-d, --delimiter` | `_`, `-`, or space (default: `-`) |
| `-v, --verbose` | Enable verbose logging |

---

### Prompt Control

| Option | Description |
|------|-------------|
| `-p, --prompt` | Append text to the default prompt |
| `-o, --override` | Replace the entire prompt |

⚠️ **`--prompt` and `--override` are mutually exclusive**

---

### Model Session Control

| Option | Description |
|------|-------------|
| `-k, --keep` | Do not reset the model conversation |

By default, the conversation is reset before processing images.

---

### Metadata / EXIF Options

| Option | Description |
|------|-------------|
| `-mt, --metadata` | Parse metadata using external `exiftool` (requires to install it, e.g., ``brew install exiftool``) |
| `-mp, --metadata-python` | Parse metadata using Python libraries |

When enabled, selected metadata fields (camera, flash, GPS, etc.) are appended to the prompt to improve keyword accuracy. You can configure which EXIF tags are included by editing:

```python
metadata_filter = [
  "Date/Time Original",
  "Flash",
  "Make",
  "Camera Model Name",
  "Orientation",
  "GPS Position"
]
```

Note: tests reveal that using ``exiftool`` enables a more accurate parsing of the tags, especially the GPS location. 

### File date, directory, etc

| Option | Description |
|------|-------------|
| `-dir, --directory-name` | Passes the directory name to the prompt for clues | 
| `--t, --timestamp` | Passes the date of the image (as per file system / OS) to the prompt | 

### Renaming files with prefixes, timestamps, postfixes, etc.

| Option | Description |                                    
|------|-------------|
| `--pre, --prefix` | Passes a string as prefix for all files | 
| `--pretime, --prefix-timestamp` | Passes the file's timestamp string as prefix for each file (if you want a current time, you can consider using ``--prefix $(date +%d-%m-%Y)`` | 
| ``--post, --postfix | Same as above but appends at the end | 
| ``--posttime, --postfix-timestamp | | Same as above but appends at the end | 

## Prompt Design

The tool uses a structured prompt to ensure the AI returns machine-readable output.

### Default Prompt

```python
Describe the image in {number} simple keywords, never use more than {number} words.
Output in JSON format.
Use the following schema: { keywords: List[str] }.
```

- `{number}` is dynamically replaced using the `-n / --number` argument.
- The model **must** return valid JSON matching the specified schema.
- The prompt is intentionally strict to allow automatic parsing.

---

### Modifying the Prompt

You can customize how images are described in two ways:

#### Append to the default prompt

Use `-p / --prompt` to add additional instructions while keeping the original prompt structure:

```bash
python3 ai_rename_images.py ./images -p "Focus on architectural features of the buildings you see."
```

## Supported File Types

  * ✅ .jpg
  * ✅ .jpeg
  * ❌ Everything else is ignored

### Core dependencies include:

  * ``ollama`` 
  * ``pydantic``
  * ``tqdm``

### Optional dependencies (loaded dynamically as needed)

  * ``pillow`` (only if using --metadata-python mode)
  * ``geopy``, ``lat-lon-parser``, ``pandas`` (for GPS parsing while using --metadata mode) 

## Credits

This project is a fork of [ollama-rename-img](https://github.com/Tedfulk/ollama-rename-img) but with some major differences: (1) model selection, (2) prompt customization, (3) pip-based dependencies, (4) GPS or metadata passed to prompt, and also, some minor differences: (1) disregards ``.DS_store`` or any non-jpeg files, (2) removes extra files from loading bar. 

Additional snippets of code from:
  * A one liner by [Vaibhav K, from stackoverflow](https://stackoverflow.com/questions/21697645/how-to-extract-metadata-from-an-image-using-python) was modified to invoke exiftool and grab metadata tags.
  * Image samples from [exif-samples](https://github.com/ianare/exif-samples/blob/master/jpg/gps/DSCN0010.jpg) were used to test GPS tags when extracted frim exif metadata.

# License

Same license as the original project unless otherwise specified.

