"""GradeFlow · a local, interactive Student Grade & GPA Tracker.

Run: python -m streamlit run app.py
"""

import csv
import io
import os
import sqlite3
from html import escape
from pathlib import Path

import streamlit as st

from database import GradebookStore
from tracker import GPA_SCALE, calculate_course, calculate_gpa, grade_to_gpa


st.set_page_config(
    page_title="GradeFlow · Student Grade Tracker",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stAppViewContainer"] {font-family: 'DM Sans', sans-serif;}
h1, h2, h3 {font-family:'Outfit',sans-serif;letter-spacing:-.025em;}
.block-container {padding-top:1.65rem;max-width:1190px;}
[data-testid="stSidebar"] {border-right:1px solid #e7eaf4;}
[data-testid="stSidebar"] .block-container {padding-top:1.5rem;}
.hero {background:linear-gradient(120deg,#242b66,#5057c9 65%,#7773e7);
       border-radius:22px;padding:30px 34px;color:white;margin:4px 0 26px;
       box-shadow:0 12px 35px rgba(47,54,131,.16);}
.hero .eyebrow {opacity:.75;letter-spacing:.14em;font-size:11px;font-weight:800;margin-bottom:8px;}
.hero h1 {color:white;font-size:34px;line-height:1.2;margin:0 0 6px;letter-spacing:-.035em;}
.hero p {color:#e6e8ff;margin:0;font-size:14px;}
.section-kicker {text-transform:uppercase;letter-spacing:.10em;color:#8a8fa9;font-size:11px;font-weight:800;}
.pill {display:inline-block;border-radius:40px;font-size:12px;padding:4px 10px;font-weight:800;
       background:#eef0ff;color:#5b5bb3;}
.pill.done {background:#e6f8ee;color:#18734b;}
[data-testid="stMetric"] {background:#fff;border:1px solid #e8eaf3;border-radius:16px;padding:18px 20px;
                           box-shadow:0 6px 18px rgba(33,45,93,.035);min-height:126px;}
[data-testid="stMetricLabel"] p{color:#69708e;font-weight:600;font-size:13px;}
[data-testid="stMetricValue"] {font-family:'Outfit',sans-serif;font-size:33px;font-weight:800;}
[data-testid="stForm"] {border-radius:16px;border:1px solid #e7eaf4;background:white;padding:17px;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#e7eaf4;border-radius:17px;}
.note {background:#f0f1ff;border:1px solid #e0e3ff;color:#474e87;border-radius:12px;padding:10px 14px;font-size:13px;margin:6px 0 15px;}
.mini-title {font-weight:800;color:#28304f;font-size:16px;}
[data-testid="stProgress"]>div>div>div {background-color:#6865de;}
</style>
""", unsafe_allow_html=True)


def get_store() -> GradebookStore:
    path = Path(os.environ.get("GRADEFLOW_DB_PATH", "data/gradeflow.sqlite3"))
    if "gradebook" not in st.session_state:
        st.session_state.gradebook = GradebookStore(path)
    return st.session_state.gradebook


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8-sig")


def error_message(exc: Exception):
    if isinstance(exc, sqlite3.IntegrityError):
        st.error("This course code already exists for that term, or a database constraint was violated.")
    else:
        st.error(str(exc))


def course_results(courses: list[dict], store: GradebookStore) -> list[dict]:
    output = []
    for course in courses:
        assessments = store.list_assessments(course["id"])
        result = calculate_course(assessments)
        output.append({**course, "assessments": assessments, "result": result})
    return output


store = get_store()
all_courses = store.list_courses()
terms = store.list_terms()

with st.sidebar:
    st.markdown("### 🎓 GradeFlow")
    st.caption("Your academic progress, organized.")
    st.divider()
    selected_term = st.selectbox("Academic term", ["All terms"] + terms)
    st.caption("Filter the dashboard, courses, and insights by term.")
    st.divider()
    st.markdown("**About GPA estimates**")
    st.caption("Uses an illustrative 4.0 scale. GPA includes only courses with 100% of their assessments graded. Check your school's official scale before relying on it.")
    with st.expander("View GPA scale"):
        for lower, letter, points in GPA_SCALE:
            st.caption(f"{lower:>2}%+ · {letter} · {points:.1f} points")
    st.divider()
    st.caption("🔒 Data stays in a SQLite file on this computer. This app has no user accounts or cloud sync.")

filtered_courses = store.list_courses(None if selected_term == "All terms" else selected_term)
rows = course_results(filtered_courses, store)
completed = [row for row in rows if row["result"].is_complete]
gpa = calculate_gpa((row["result"].final_percentage, row["credits"]) for row in completed)

st.markdown("""
<div class="hero">
<div class="eyebrow">YOUR STUDY COMPANION</div>
<h1>Make every grade count.</h1>
<p>Track courses, calculate weighted averages, and see where you stand.</p>
</div>
""", unsafe_allow_html=True)

summary, manage, insights, data = st.tabs(["📊  Overview", "📚  Courses & grades", "📈  Insights", "⬇️  Export & settings"])

with summary:
    a, b, c, d = st.columns(4)
    with a:
        st.metric("Total courses", len(rows))
    with b:
        st.metric("Graded assessments", sum(len(r["assessments"]) for r in rows))
    with c:
        st.metric("Completed courses", f"{len(completed)} / {len(rows)}")
    with d:
        st.metric("Estimated GPA / 4.0", "—" if gpa is None else f"{gpa:.2f}")

    st.write("")
    st.markdown("### Course progress")
    if not rows:
        with st.container(border=True):
            st.markdown("#### Welcome to GradeFlow 👋")
            st.write("Your gradebook is empty. Create your first course in **Courses & grades**, or try synthetic demo data to explore the dashboard.")
            if st.button("✨ Load example courses", type="primary"):
                try:
                    store.load_demo()
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    else:
        for i in range(0, len(rows), 2):
            cols = st.columns(2, gap="medium")
            for col, row in zip(cols, rows[i:i + 2]):
                r = row["result"]
                with col, st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"<span class='mini-title'>{escape(row['code'])} · {escape(row['name'])}</span>", unsafe_allow_html=True)
                        st.caption(f"{row['term']}  ·  {row['credits']:g} credits")
                    with col2:
                        st.markdown('<span class="pill done">Final</span>' if r.is_complete else '<span class="pill">In progress</span>', unsafe_allow_html=True)
                    grade_text = "No grades yet" if r.current_average is None else f"{r.current_average:.1f}% current average"
                    st.markdown(f"**{grade_text}**")
                    st.progress(min(1.0, r.graded_weight / 100))
                    st.caption(f"{r.graded_weight:g}% of assessment weight graded · {r.remaining_weight:g}% remaining")
                    if r.is_complete:
                        letter, gp = grade_to_gpa(r.final_percentage)
                        st.caption(f"Illustrative letter grade: {letter} · {gp:.1f} GPA points")
        st.info("**Current average** is calculated only from entered assessments. It is not your final course grade until the recorded assessment weights total 100%.")

with manage:
    st.markdown("### Add a course")
    with st.form("new_course", clear_on_submit=True):
        a, b = st.columns(2)
        with a:
            code = st.text_input("Course code", placeholder="e.g. PY101")
            term = st.text_input("Term", placeholder="e.g. Fall 2026")
        with b:
            name = st.text_input("Course name", placeholder="e.g. Python Programming")
            credits = st.number_input("Credits", min_value=0.5, max_value=24.0, value=3.0, step=0.5)
        submitted = st.form_submit_button("+ Add course", type="primary", use_container_width=True)
        if submitted:
            try:
                store.create_course(code, name, term, credits)
                st.rerun()
            except (ValueError, sqlite3.IntegrityError) as exc:
                error_message(exc)

    st.divider()
    st.markdown("### Manage assessments")
    all_for_selector = store.list_courses()
    if not all_for_selector:
        st.info("Create a course first to start adding grades.")
    else:
        options = {course["id"]: f"{course['code']} · {course['name']} ({course['term']})" for course in all_for_selector}
        cid = st.selectbox("Select course", options=list(options), format_func=lambda option: options[option], key="course_selected")
        active = next(item for item in all_for_selector if item["id"] == cid)
        assessments = store.list_assessments(cid)
        result = calculate_course(assessments)
        left, right = st.columns([1, 1])
        with left:
            st.metric("Current average", "—" if result.current_average is None else f"{result.current_average:.1f}%")
        with right:
            st.metric("Weight still available", f"{result.remaining_weight:g}%")

        with st.form(f"add_assessment_{cid}", clear_on_submit=True):
            st.markdown("**Record a new assessment**")
            a, b, c = st.columns([2, 1, 1])
            with a:
                item_name = st.text_input("Assessment", placeholder="e.g. Midterm")
            with b:
                item_score = st.number_input("Score (%)", min_value=0.0, max_value=100.0, value=80.0, step=0.5)
            with c:
                item_weight = st.number_input("Course weight (%)", min_value=0.5, max_value=100.0, value=10.0, step=0.5)
            if st.form_submit_button("+ Save assessment", type="primary", use_container_width=True):
                try:
                    store.create_assessment(cid, item_name, item_score, item_weight)
                    st.rerun()
                except (ValueError, sqlite3.IntegrityError) as exc:
                    error_message(exc)
        st.write("")
        if assessments:
            st.markdown("**Recorded assessments**")
            for entry in assessments:
                c1, c2, c3, c4 = st.columns([4, 1.5, 1.5, 1.2], vertical_alignment="center")
                with c1:
                    st.markdown(f"**{escape(entry['name'])}**")
                with c2:
                    st.write(f"{entry['score']:g}%")
                with c3:
                    st.caption(f"Weight {entry['weight']:g}%")
                with c4:
                    if st.button("Remove", key=f"remove_assessment_{entry['id']}"):
                        store.delete_assessment(entry["id"])
                        st.rerun()
            with st.expander("✏️ Edit an existing assessment"):
                by_id = {a["id"]: a for a in assessments}
                aid = st.selectbox("Assessment to edit", list(by_id), format_func=lambda k: by_id[k]["name"])
                chosen = by_id[aid]
                with st.form(f"edit_assessment_{aid}"):
                    edit_name = st.text_input("Assessment name", value=chosen["name"])
                    edit_score = st.number_input("Score (%)", min_value=0.0, max_value=100.0,
                                                 value=float(chosen["score"]), step=0.5)
                    edit_weight = st.number_input("Weight (%)", min_value=0.01, max_value=100.0,
                                                  value=float(chosen["weight"]), step=0.5)
                    if st.form_submit_button("Save assessment changes"):
                        try:
                            store.update_assessment(aid, edit_name, edit_score, edit_weight)
                            st.rerun()
                        except (ValueError, sqlite3.IntegrityError) as exc:
                            error_message(exc)
        else:
            st.caption("No assessments recorded yet for this course.")
        with st.expander("⚙️ Edit course details"):
            with st.form(f"edit_course_{cid}"):
                ed_code = st.text_input("Course code", value=active["code"])
                ed_name = st.text_input("Course name", value=active["name"])
                ed_term = st.text_input("Term", value=active["term"])
                ed_credits = st.number_input("Credits", min_value=0.5, max_value=24.0,
                                              value=float(active["credits"]), step=0.5)
                if st.form_submit_button("Save course changes"):
                    try:
                        store.update_course(cid, ed_code, ed_name, ed_term, ed_credits)
                        st.rerun()
                    except (ValueError, sqlite3.IntegrityError) as exc:
                        error_message(exc)
        with st.expander("🗑️ Delete this course"):
            st.warning("This permanently deletes the course AND all its recorded assessments.")
            confirm_course_delete = st.checkbox("Yes, delete this course and its grades", key=f"confirm_{cid}")
            if st.button("Delete course", disabled=not confirm_course_delete):
                store.delete_course(cid)
                st.rerun()

with insights:
    st.markdown("### Performance insights")
    if not rows:
        st.info("Add assessments or load demo data to view insights.")
    else:
        import pandas as pd  # pandas is included with Streamlit

        chart_data = [
            {"Course": f"{r['code']} · {r['term']}", "Current average (%)": round(r["result"].current_average, 2)}
            for r in rows if r["result"].current_average is not None
        ]
        if chart_data:
            st.markdown("**Current averages by course**")
            df = pd.DataFrame(chart_data)
            st.bar_chart(df, x="Course", y="Current average (%)", color="#6a66e5")
        else:
            st.info("No grade data has been added yet.")
        st.markdown("**Course-level details**")
        detail_rows = []
        for row in rows:
            result = row["result"]
            details = {
                "Course": row["code"], "Term": row["term"], "Credits": row["credits"],
                "Graded weight (%)": result.graded_weight,
                "Current average (%)": None if result.current_average is None else round(result.current_average, 2),
                "Status": "Complete" if result.is_complete else "In progress",
                "GPA points": grade_to_gpa(result.final_percentage)[1] if result.is_complete else None,
            }
            detail_rows.append(details)
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
        st.markdown('<div class="note">Only completed courses contribute to the GPA. In-progress courses display their current average based on the assessments entered.</div>', unsafe_allow_html=True)

with data:
    st.markdown("### Export your data")
    st.write("Download your own course summary and assessment records as CSV files. Both files open in Excel or Google Sheets.")
    all_results = course_results(store.list_courses(), store)
    summary_rows = []
    for row in all_results:
        result = row["result"]
        summary_rows.append({
            "term": row["term"], "code": row["code"], "course_name": row["name"],
            "credits": row["credits"], "graded_weight_percent": result.graded_weight,
            "current_average_percent": "" if result.current_average is None else round(result.current_average, 2),
            "final_grade_percent": "" if result.final_percentage is None else round(result.final_percentage, 2),
            "gpa_points_estimate": "" if not result.is_complete else grade_to_gpa(result.final_percentage)[1],
        })
    a, b = st.columns(2)
    with a:
        st.download_button("⬇️ Download course summary CSV", data=csv_bytes(summary_rows, [
            "term", "code", "course_name", "credits", "graded_weight_percent",
            "current_average_percent", "final_grade_percent", "gpa_points_estimate",
        ]), file_name="gradeflow_course_summary.csv", mime="text/csv", use_container_width=True)
    with b:
        st.download_button("⬇️ Download assessments CSV", data=csv_bytes(store.all_assessments(), [
            "term", "course_code", "course_name", "name", "score", "weight",
        ]), file_name="gradeflow_assessments.csv", mime="text/csv", use_container_width=True)
    st.caption("Exports contain your information; keep them private unless you choose to share them.")
    st.divider()
    st.markdown("### Settings")
    st.write("The GPA scale is defined in `tracker.py` and is for demonstration purposes only.")
    with st.expander("Clear all locally saved data"):
        st.warning("This cannot be undone. Export your records first if you want a backup.")
        confirmed = st.checkbox("I understand that all courses and assessments will be deleted")
        if st.button("Delete all grade data", disabled=not confirmed, type="secondary"):
            store.clear()
            st.rerun()

st.write("")
st.caption("GradeFlow · Built with Python, Streamlit & SQLite · Local-first, portfolio-ready")
