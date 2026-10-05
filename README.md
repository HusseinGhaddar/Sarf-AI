# Sarf-AI

An experimental Arabic **إعراب** analyzer built with Python, Flask, Stanza, and CAMeL Tools. It combines morphological analysis, dependency parsing, and handcrafted grammatical rules through a browser interface.

## Current scope

- Accepts Arabic sentences containing **two or three words**.
- Removes diacritics and tatweel before analysis.
- Rejects non-Arabic characters and punctuation in the web form.
- Applies rules for selected nominal and verbal sentence patterns.
- Shows Arabic validation messages and a fallback when no rule matches.

**Status: experimental / in development.** The rule set covers selected patterns; it is not a general-purpose Arabic parser, and no accuracy benchmark is included.

## How it works

1. The Flask app validates and normalizes the input.
2. CAMeL Tools provides tokenization and morphological analysis.
3. Stanza supplies Arabic part-of-speech tags and dependency parsing.
4. The rule engine produces an Arabic grammatical explanation for recognized patterns.

## Repository structure

```text
Sarf AI/
  app.py                 Flask routes, validation, and development server
  sarf.py                NLP initialization and grammar rules
  templates/index.html   Browser interface
```

## Local setup

Check the [CAMeL Tools installation prerequisites](https://camel-tools.readthedocs.io/en/latest/getting_started.html) for your operating system before installing; current releases require a supported 64-bit Python version and native build dependencies.

The repository does not yet include a pinned dependency manifest. The following commands reflect the imports and model requirements in the source; environment compatibility and setup still need validation.

```bash
git clone https://github.com/HusseinGhaddar/Sarf-AI.git
cd Sarf-AI
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install the Python packages and model data:

```bash
python -m pip install flask stanza camel-tools
python -c "import stanza; stanza.download('ar')"
camel_data -i light
cd "Sarf AI"
python app.py
```

Open **http://localhost:5000**. Model resources are loaded during startup; missing resources can prevent the app from starting.

## Development notes

- The entry point runs Flask's development server with debug mode enabled.
- The rule engine currently prints analysis details to the terminal.
- Broader sentence coverage, reproducible dependency versions, and an evaluation dataset are future improvements.
