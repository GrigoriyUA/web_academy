# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
cd calculator
pip install flask
python app.py
```

The server starts at `http://127.0.0.1:5000` and opens the browser automatically.

## Architecture

**`calculator/app.py`** — Flask backend with two routes:
- `GET /` — serves `templates/index.html`
- `POST /calculate` — receives `{ "expression": "..." }`, validates input against a character whitelist, runs `eval()`, returns `{ "result": ... }` or `{ "error": ... }`

**`calculator/templates/index.html`** — single-page frontend. Uses `fetch('/calculate')` to send expressions to the Python backend. Also contains a `<canvas>` binary rain animation (pure JS). No external JS frameworks.
