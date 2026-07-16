# ETEA Streamlit Quiz App — Results Dashboard Version

This version does three things:

1. Lets the candidate take the MCQ test.
2. Saves their name/email, score, selected answers, correct answers, and correct/wrong status.
3. Gives you an Admin Results dashboard where you can inspect and download results.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Candidate mode

Select **Candidate Test** in the sidebar. The candidate enters name/email, starts the test, selects A/B/C/D, and submits.

## Admin mode

Select **Admin Results** in the sidebar.

Default password:

```text
admin123
```

Change this before sharing the app publicly.

## Stored files

After submissions, these files are created automatically:

- `summary.csv` — one row per candidate submission
- `responses.csv` — one row per question per candidate

The admin dashboard also includes download buttons for these files.

## Important note for online use

This CSV-based version is simple and good for testing or supervised use. If you deploy to Streamlit Cloud, the CSV files are stored on the cloud app environment, not automatically on your laptop. Download results regularly from the Admin Results page.

For a more permanent online solution, connect the app to Google Sheets or a database.

## Change exam duration

Open `app.py` and change:

```python
DURATION_MINUTES = 90
```

## Change admin password locally

Open `app.py` and change the fallback password:

```python
return "admin123"
```

## Change admin password on Streamlit Cloud

Add a secret named:

```toml
ADMIN_PASSWORD = "your_strong_password"
```
