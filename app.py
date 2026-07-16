import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

QUESTIONS_FILE = Path("questions.json")
RESPONSES_FILE = Path("responses.csv")
SUMMARY_FILE = Path("summary.csv")

DURATION_MINUTES = 90

# Change this password before using the app with real candidates.
# On Streamlit Cloud, preferably set ADMIN_PASSWORD in app secrets.
def get_admin_password():
    try:
        return st.secrets.get("ADMIN_PASSWORD", "admin123")
    except Exception:
        return "admin123"

ADMIN_PASSWORD = get_admin_password()

st.set_page_config(page_title="ETEA Practice Test", page_icon="📝", layout="wide")

st.markdown("""
<style>
.block-container { max-width: 1050px; padding-top: 2rem; padding-bottom: 3rem; }
h1 { text-align: center; color: #1f2a44; }
h2, h3 { color: #1f2a44; margin-top: 2rem; }
div[data-testid="stRadio"] label { font-size: 16px; }
.option-line { margin: 0.2rem 0 0.45rem 0; font-size: 1.02rem; }
.timer-box { position: sticky; top: 0; z-index: 999; padding: 10px 14px; border-radius: 10px; background: #fff7ed; border: 1px solid #fed7aa; color: #9a3412; font-weight: 800; text-align: center; margin-bottom: 16px; }
.result-ok { color: #166534; font-weight: 800; }
.result-bad { color: #991b1b; font-weight: 800; }
.result-missing { color: #92400e; font-weight: 800; }
.small-muted { color: #6b7280; font-size: 0.9rem; }
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
        rows.append({
            "question_id": q["id"],
            "section": q["section"],
            "selected": selected,
            "correct_answer": q["answer"],
            "is_correct": is_correct,
        })
    return correct, rows


def append_csv(path, row_dict):
    df = pd.DataFrame([row_dict])
    df.to_csv(path, mode="a" if path.exists() else "w", header=not path.exists(), index=False)


def save_detailed_response(candidate_name, candidate_email, score, total, detail_rows):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    percentage = round(score / total * 100, 2)

    for row in detail_rows:
        append_csv(RESPONSES_FILE, {
            "timestamp": timestamp,
            "candidate_name": candidate_name,
            "candidate_email": candidate_email,
            "score": score,
            "total": total,
            "percentage": percentage,
            **row,
        })

    append_csv(SUMMARY_FILE, {
        "timestamp": timestamp,
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "score": score,
        "total": total,
        "percentage": percentage,
    })


def format_time(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def read_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def option_text(q, letter):
    if not letter or letter not in q["options"]:
        return "Not answered"
    return q["options"][letter]


def render_candidate_feedback(questions, details_df):
    q_by_id = {int(q["id"]): q for q in questions}

    filter_choice = st.radio(
        "Show questions:",
        ["All", "Wrong only", "Correct only", "Unanswered only"],
        horizontal=True,
    )

    rows = details_df.sort_values("question_id").to_dict("records")
    shown = 0

    for row in rows:
        qid = int(row["question_id"])
        q = q_by_id.get(qid)
        if not q:
            continue

        selected = "" if pd.isna(row.get("selected", "")) else str(row.get("selected", ""))
        correct_answer = str(row.get("correct_answer", ""))
        is_correct = bool(row.get("is_correct", False))
        unanswered = selected == ""

        if filter_choice == "Wrong only" and (is_correct or unanswered):
            continue
        if filter_choice == "Correct only" and not is_correct:
            continue
        if filter_choice == "Unanswered only" and not unanswered:
            continue

        shown += 1
        status_html = '<span class="result-ok">Correct</span>' if is_correct else ('<span class="result-missing">Unanswered</span>' if unanswered else '<span class="result-bad">Wrong</span>')

        with st.expander(f"Q{qid} — {q['section']} — {'Correct' if is_correct else ('Unanswered' if unanswered else 'Wrong')}", expanded=not is_correct):
            st.markdown(q["question"])

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**A)** {q['options']['A']}")
                st.markdown(f"**B)** {q['options']['B']}")
            with c2:
                st.markdown(f"**C)** {q['options']['C']}")
                st.markdown(f"**D)** {q['options']['D']}")

            st.markdown(f"Result: {status_html}", unsafe_allow_html=True)
            st.markdown(f"Candidate selected: **{selected if selected else 'Not answered'}** — {option_text(q, selected)}")
            st.markdown(f"Correct answer: **{correct_answer}** — {option_text(q, correct_answer)}")

    if shown == 0:
        st.info("No questions match this filter.")


def build_feedback_table(questions, details_df):
    q_by_id = {int(q["id"]): q for q in questions}
    output_rows = []

    for row in details_df.sort_values("question_id").to_dict("records"):
        qid = int(row["question_id"])
        q = q_by_id.get(qid)
        if not q:
            continue
        selected = "" if pd.isna(row.get("selected", "")) else str(row.get("selected", ""))
        correct_answer = str(row.get("correct_answer", ""))
        output_rows.append({
            "question_id": qid,
            "section": q["section"],
            "selected": selected if selected else "Not answered",
            "selected_option_text": option_text(q, selected),
            "correct_answer": correct_answer,
            "correct_option_text": option_text(q, correct_answer),
            "is_correct": bool(row.get("is_correct", False)),
        })
    return pd.DataFrame(output_rows)


questions = load_questions()

with st.sidebar:
    app_mode = st.selectbox("Mode", ["Candidate Test", "Admin Results"])


if app_mode == "Admin Results":
    st.title("Admin Results Dashboard")
    password = st.text_input("Admin password", type="password")

    if password != ADMIN_PASSWORD:
        st.info("Enter the admin password to view stored results.")
        st.warning("Default password is admin123. Change it before sharing the app publicly.")
        st.stop()

    st.success("Admin access granted.")

    summary_df = read_csv_if_exists(SUMMARY_FILE)
    responses_df = read_csv_if_exists(RESPONSES_FILE)

    if summary_df.empty:
        st.info("No submissions yet. After a candidate submits, results will appear here.")
        st.stop()

    st.subheader("Summary of submissions")
    st.dataframe(summary_df.sort_values("timestamp", ascending=False), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download summary.csv",
            data=summary_df.to_csv(index=False).encode("utf-8"),
            file_name="summary.csv",
            mime="text/csv",
        )
    with col2:
        st.download_button(
            "Download responses.csv",
            data=responses_df.to_csv(index=False).encode("utf-8"),
            file_name="responses.csv",
            mime="text/csv",
        )

    st.divider()
    st.subheader("Candidate-level feedback")

    sorted_summary = summary_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    labels = [
        f"{r['timestamp']} | {r['candidate_name']} | {r.get('candidate_email', '')} | {r['score']}/{r['total']} ({r['percentage']}%)"
        for _, r in sorted_summary.iterrows()
    ]
    selected_label = st.selectbox("Select candidate submission", labels)
    selected_row = sorted_summary.iloc[labels.index(selected_label)]

    mask = (
        (responses_df["timestamp"].astype(str) == str(selected_row["timestamp"]))
        & (responses_df["candidate_name"].astype(str) == str(selected_row["candidate_name"]))
        & (responses_df["candidate_email"].fillna("").astype(str) == str(selected_row.get("candidate_email", "")))
    )
    candidate_details = responses_df[mask].copy()

    st.markdown(
        f"**{selected_row['candidate_name']}** scored **{selected_row['score']}/{selected_row['total']}** "
        f"(**{selected_row['percentage']}%**)."
    )

    feedback_df = build_feedback_table(questions, candidate_details)
    wrong_count = int((feedback_df["is_correct"] == False).sum())
    correct_count = int((feedback_df["is_correct"] == True).sum())
    unanswered_count = int((feedback_df["selected"] == "Not answered").sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Correct", correct_count)
    m2.metric("Wrong / unanswered", wrong_count)
    m3.metric("Unanswered", unanswered_count)

    st.download_button(
        "Download this candidate feedback CSV",
        data=feedback_df.to_csv(index=False).encode("utf-8"),
        file_name=f"feedback_{selected_row['candidate_name']}.csv".replace(" ", "_"),
        mime="text/csv",
    )

    render_candidate_feedback(questions, candidate_details)
    st.stop()


# Candidate test mode
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
            selected_answer = st.radio(
                "Select your answer:",
                ["A", "B", "C", "D"],
                index=None,
                horizontal=True,
                key=f"q_{q['id']}",
                disabled=remaining <= 0,
            )
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
