# ETEA Streamlit Quiz App — LaTeX Updated Version

This version displays mathematical expressions in proper equation format using Streamlit Markdown/LaTeX.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Main changes

- Mathematical expressions are written with LaTeX in `questions.json`.
- Questions/options are rendered with `st.markdown()`.
- Candidate selects only A/B/C/D.
- The visible “Not answered” option has been removed.

## Edit timer

Open `app.py` and change:

```python
DURATION_MINUTES = 90
```

## Editing math in questions.json

Use double backslashes in JSON, for example:

```json
"question": "$\frac{1+i}{1-i}$ is equal to:"
```
