# Roadsafety Backend

This project uses a workspace virtual environment at `.venv`.

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\activate
python main.py
```

The backend will start on `http://0.0.0.0:8000`.

## Notes

- `main.py` now uses the installed `langchain_classic` chain imports.
- If you do not have an Anthropic API key, comment out the Anthropic LLM code or set `ANTHROPIC_API_KEY`.
- If you encounter missing packages again, reinstall with `pip install -r requirements.txt`.
