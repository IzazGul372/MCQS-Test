import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

QUESTIONS_FILE = Path("questions.json")
RESPONSES_FILE = Path("responses.csv")
SUMMARY_FILE = Path("summary.csv")

DURATION_MINUTES = 90

st.set_page_config(page_title="ETEA Practice Test", page_icon="📝", layout="wide")

st.markdown("""
<style>
.block-container { max-width: 1000px; padding-top: 2rem; padding-bottom: 3rem; }
h1 { text-align: center; color: #1f2a44; }
h2, h3 { color: #1f2a44; margin-top: 2rem; }
div[data-testid="stRadio"] label { font-size: 16px; }
.option-line { margin: 0.2rem 0 0.45rem 0; font-size: 1.02rem; }
.timer-box { position: sticky; top: 0; z-index: 999; padding: 10px 14px; border-radius: 10px; background: #fff7ed; border: 1px solid #fed7aa; color: #9a3412; font-weight: 800; text-align: center; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)

def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_score(questions, answers):
    correct = 0
    rows = []
    for q in questions:
        qid = str(q["id"])
        selected = answers.get(qid, "")
        is_correct = selected == q["answer"]
        correct += int(is_correct)
        rows.append({"question_id": q["id"], "section": q["section"], "selected": selected, "correct_answer": q["answer"], "is_correct": is_correct})
    return correct, rows

def append_csv(path, row_dict):
    df = pd.DataFrame([row_dict])
    df.to_csv(path, mode="a" if path.exists() else "w", header=not path.exists(), index=False)

def save_detailed_response(candidate_name, candidate_email, score, total, detail_rows):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in detail_rows:
        append_csv(RESPONSES_FILE, {"timestamp": timestamp, "candidate_name": candidate_name, "candidate_email": candidate_email, "score": score, "total": total, **row})
    append_csv(SUMMARY_FILE, {"timestamp": timestamp, "candidate_name": candidate_name, "candidate_email": candidate_email, "score": score, "total": total, "percentage": round(score / total * 100, 2)})

def format_time(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

questions = load_questions()

st.title("ETEA-Style Practice Test")
st.caption("Mathematical expressions are rendered in equation format. Select only A, B, C, or D for each question.")

with st.sidebar:
    st.header("Candidate Details")
    candidate_name = st.text_input("Full name")
    candidate_email = st.text_input("Email or phone/reference")
    st.divider()
    st.write(f"Total questions: **{len(questions)}**")
    st.write(f"Time allowed: **{DURATION_MINUTES} minutes**")
    st.warning("Do not refresh the page during the test.")

for key, default in {"started": False, "submitted": False, "start_time": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state.started:
    st.info("Enter candidate details, then start the test.")
    if st.button("Start Test", type="primary"):
        if not candidate_name.strip():
            st.error("Please enter candidate name before starting.")
        else:
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.rerun()
    st.stop()

if st.session_state.submitted:
    st.success("Test already submitted. Thank you.")
    st.stop()

end_time = st.session_state.start_time + timedelta(minutes=DURATION_MINUTES)
remaining = (end_time - datetime.now()).total_seconds()

st.markdown(f'<div class="timer-box">Time remaining: {format_time(remaining)}</div>', unsafe_allow_html=True)
if remaining <= 0:
    st.error("Time is over. Please submit immediately. New selections are disabled.")
if st.button("Refresh timer"):
    st.rerun()

answers = {}
sections = []
for q in questions:
    if q["section"] not in sections:
        sections.append(q["section"])

for section in sections:
    st.header(section)
    for q in [item for item in questions if item["section"] == section]:
        with st.container(border=True):
            st.markdown(f"### Q{q['id']}.")
            st.markdown(q["question"])
            st.write("")
            left, right = st.columns(2)
            with left:
                st.markdown(f"**A)** {q['options']['A']}")
                st.markdown(f"**B)** {q['options']['B']}")
            with right:
                st.markdown(f"**C)** {q['options']['C']}")
                st.markdown(f"**D)** {q['options']['D']}")
            selected_answer = st.radio("Select your answer:", ["A", "B", "C", "D"], index=None, horizontal=True, key=f"q_{q['id']}", disabled=remaining <= 0)
            answers[str(q["id"])] = selected_answer if selected_answer is not None else ""

st.divider()
unanswered = sum(1 for v in answers.values() if v == "")
st.write(f"Unanswered questions: **{unanswered}**")
confirm = st.checkbox("I confirm that I want to submit my test.")
submit_clicked = st.button("Submit Test", type="primary", disabled=not confirm)

if submit_clicked:
    if not candidate_name.strip():
        st.error("Candidate name is missing.")
    else:
        score, detail_rows = calculate_score(questions, answers)
        save_detailed_response(candidate_name.strip(), candidate_email.strip(), score, len(questions), detail_rows)
        st.session_state.submitted = True
        st.success("Test submitted successfully.")
        st.write(f"Score saved: **{score}/{len(questions)}**")
        st.info("You may now close this page.")
