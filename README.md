# ETEA Streamlit Quiz App — JSON Results Version

This version fixes the `pandas.errors.ParserError` that can happen when reading corrupted CSV files.

## What changed

- Candidate submissions are stored internally in `submissions.jsonl`.
- Each candidate submission is saved as one JSON line.
- The Admin Results dashboard converts this data into downloadable CSV files.
- If a stored line is corrupted, the admin dashboard skips it instead of crashing.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Admin login

Default password:

```text
admin123
```

Change this before sharing the test.

On Streamlit Cloud, set a secret:

```toml
ADMIN_PASSWORD = "your_new_password"
```

## Result files

The app creates:

```text
submissions.jsonl
```

From the Admin Results dashboard, you can download:

- `summary.csv`
- `responses.csv`
- individual candidate feedback CSV
- raw `submissions.jsonl`

## Important

If you previously used an older CSV version and got `pandas.errors.ParserError`, replace your deployed files with this version. Old `summary.csv` and `responses.csv` are no longer used by this app.
