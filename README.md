# ETEA Streamlit Quiz App

A minimal quiz app for your MCQ test.

## Install

```bash
pip install -r requirements.txt
```

## Run locally

```bash
streamlit run app.py
```

## What gets saved

After submission:

- `summary.csv` contains candidate name/email and total score.
- `responses.csv` contains each answer and whether it was correct.

## Change timer

Open `app.py` and change:

```python
DURATION_MINUTES = 90
```

## Share with someone on the same Wi-Fi

```bash
streamlit run app.py --server.address 0.0.0.0
```

Then open your local IP address with port 8501, for example:

```text
http://192.168.1.10:8501
```

For online sharing, deploy the folder to Streamlit Community Cloud, Render, or another hosting service.
