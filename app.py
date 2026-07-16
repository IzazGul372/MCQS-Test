import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

QUESTIONS_FILE = Path("questions.json")
SUBMISSIONS_FILE = Path("submissions.jsonl")

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


def save_submission(candidate_name, candidate_email, score, total, detail_rows):
    """Save one full submission as one JSON line.
    This is more robust than appending many CSV rows and avoids pandas ParserError.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    submission = {
        "timestamp": timestamp,
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "score": score,
        "total": total,
        "percentage": round(score / total * 100, 2),
        "details": detail_rows,
    }
    with open(SUBMISSIONS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(submission, ensure_ascii=False) + "\n")


def load_submissions():
    """Load JSONL submissions. Bad/corrupted lines are skipped instead of crashing admin page."""
    submissions = []
    skipped = 0
    if not SUBMISSIONS_FILE.exists():
        return submissions, skipped
    with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                submissions.append(json.loads(line))
            except json.JSONDecodeError:
                skipped += 1
    return submissions, skipped


def submissions_to_summary_df(submissions):
    rows = []
    for s in submissions:
        rows.append({
            "timestamp": s.get("timestamp", ""),
            "candidate_name": s.get("candidate_name", ""),
            "candidate_email": s.get("candidate_email", ""),
            "score": s.get("score", 0),
            "total": s.get("total", 0),
            "percentage": s.get("percentage", 0),
        })
    return pd.DataFrame(rows)


def submissions_to_responses_df(submissions):
    rows = []
    for s in submissions:
        for d in s.get("details", []):
            rows.append({
                "timestamp": s.get("timestamp", ""),
                "candidate_name": s.get("candidate_name", ""),
                "candidate_email": s.get("candidate_email", ""),
                "score": s.get("score", 0),
                "total": s.get("total", 0),
                "percentage": s.get("percentage", 0),
                "question_id": d.get("question_id", ""),
                "section": d.get("section", ""),
                "selected": d.get("selected", ""),
                "correct_answer": d.get("correct_answer", ""),
                "is_correct": d.get("is_correct", False),
            })
    return pd.DataFrame(rows)


def format_time(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


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

    if details_df.empty:
        st.info("No detailed response rows found for this candidate.")
        return

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

    submissions, skipped = load_submissions()
    if skipped:
        st.warning(f"Skipped {skipped} corrupted saved submission line(s). The dashboard will still load.")

    if not submissions:
        st.info("No submissions yet. After a candidate submits, results will appear here.")
        st.stop()

    summary_df = submissions_to_summary_df(submissions)
    responses_df = submissions_to_responses_df(submissions)

    st.subheader("Summary of submissions")
    st.dataframe(summary_df.sort_values("timestamp", ascending=False), use_container_width=True)

    col1, col2, col3 = st.columns(3)
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
    with col3:
        st.download_button(
            "Download raw submissions.jsonl",
            data="\n".join(json.dumps(s, ensure_ascii=False) for s in submissions).encode("utf-8"),
            file_name="submissions.jsonl",
            mime="application/jsonl",
        )

    st.divider()
    st.subheader("Candidate-level feedback")

    sorted_summary = summary_df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    labels = [
        f"{r['timestamp']} | {r['candidate_name']} | {r.get('candidate_email', '')} | {r['score']}/{r['total']} ({r['percentage']}%)"
        for _, r in sorted_summary.iterrows()
    ]
    selected_label = st.selectbox("Select candidate submission", labels)
    selected_index = labels.index(selected_label)
    selected_row = sorted_summary.iloc[selected_index]

    selected_submission = None
    for s in submissions:
        if (
            str(s.get("timestamp", "")) == str(selected_row["timestamp"])
            and str(s.get("candidate_name", "")) == str(selected_row["candidate_name"])
            and str(s.get("candidate_email", "")) == str(selected_row.get("candidate_email", ""))
        ):
            selected_submission = s
            break

    if selected_submission is None:
        st.error("Could not find details for the selected submission.")
        st.stop()

    candidate_details = pd.DataFrame(selected_submission.get("details", []))

    st.markdown(
        f"**{selected_row['candidate_name']}** scored **{selected_row['score']}/{selected_row['total']}** "
        f"(**{selected_row['percentage']}%**)."
    )

    feedback_df = build_feedback_table(questions, candidate_details)
    wrong_count = int((feedback_df["is_correct"] == False).sum()) if not feedback_df.empty else 0
    correct_count = int((feedback_df["is_correct"] == True).sum()) if not feedback_df.empty else 0
    unanswered_count = int((feedback_df["selected"] == "Not answered").sum()) if not feedback_df.empty else 0

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
        save_submission(candidate_name.strip(), candidate_email.strip(), score, len(questions), detail_rows)
        st.session_state.submitted = True
        st.success("Test submitted successfully.")
        st.write(f"Score saved: **{score}/{len(questions)}**")
        st.info("You may now close this page.")
