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

def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def append_csv(path, row):
    df = pd.DataFrame([row])
    if path.exists():
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)

def score_test(questions, answers):
    details=[]
    score=0
    for q in questions:
        selected=answers.get(str(q["id"]), "")
        ok = selected == q["answer"]
        score += int(ok)
        details.append({"question_id":q["id"], "section":q["section"], "selected":selected,
                        "correct_answer":q["answer"], "is_correct":ok})
    return score, details

def save(candidate_name, candidate_email, score, total, details):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    append_csv(SUMMARY_FILE, {"timestamp":ts,"candidate_name":candidate_name,"candidate_email":candidate_email,
                              "score":score,"total":total,"percentage":round(score/total*100,2)})
    for d in details:
        append_csv(RESPONSES_FILE, {"timestamp":ts,"candidate_name":candidate_name,"candidate_email":candidate_email,
                                    "score":score,"total":total, **d})

def fmt(seconds):
    seconds=max(0,int(seconds)); m,s=divmod(seconds,60); h,m=divmod(m,60)
    return f"{h:02d}:{m:02d}:{s:02d}"

questions = load_questions()

st.title("ETEA-Style Practice Test")
st.caption("Select one answer for each question. Your answers will be saved after submission.")

with st.sidebar:
    st.header("Candidate")
    candidate_name = st.text_input("Full name")
    candidate_email = st.text_input("Email / phone / roll no.")
    st.divider()
    st.write(f"Questions: **{len(questions)}**")
    st.write(f"Duration: **{DURATION_MINUTES} minutes**")

if "started" not in st.session_state: st.session_state.started=False
if "submitted" not in st.session_state: st.session_state.submitted=False
if "start_time" not in st.session_state: st.session_state.start_time=None

if not st.session_state.started:
    st.warning("Enter candidate details and click Start Test.")
    if st.button("Start Test", type="primary"):
        if not candidate_name.strip():
            st.error("Please enter the candidate name.")
        else:
            st.session_state.started=True
            st.session_state.start_time=datetime.now()
            st.rerun()
    st.stop()

if st.session_state.submitted:
    st.success("Test already submitted. You may close this page.")
    st.stop()

end_time = st.session_state.start_time + timedelta(minutes=DURATION_MINUTES)
remaining = (end_time - datetime.now()).total_seconds()
st.info(f"Time remaining: **{fmt(remaining)}**")
if st.button("Refresh timer"):
    st.rerun()

if remaining <= 0:
    st.error("Time is over. Please submit immediately. The options are now locked.")

answers={}
for section in ["Mathematics", "Physics", "English"]:
    st.header(section)
    for q in [x for x in questions if x["section"] == section]:
        st.markdown(f"**Q{q['id']}. {q['question']}**")
        labels=[f"{k}) {v}" for k,v in q["options"].items()]
        selected=st.radio(f"Q{q['id']}", ["Not answered"]+labels, key=f"q_{q['id']}", label_visibility="collapsed", disabled=remaining<=0)
        answers[str(q["id"])] = "" if selected == "Not answered" else selected[0]
        st.write("")

st.divider()
unanswered=sum(1 for a in answers.values() if a == "")
st.write(f"Unanswered questions: **{unanswered}**")
confirm=st.checkbox("I confirm that I want to submit the test.")
if st.button("Submit Test", type="primary", disabled=not confirm):
    if not candidate_name.strip():
        st.error("Candidate name is missing.")
    else:
        score, details = score_test(questions, answers)
        save(candidate_name.strip(), candidate_email.strip(), score, len(questions), details)
        st.session_state.submitted=True
        st.success("Submitted successfully.")
        st.write(f"Saved score: **{score}/{len(questions)}**")
        st.info("The candidate can now close this page.")