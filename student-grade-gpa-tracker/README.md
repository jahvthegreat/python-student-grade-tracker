# 🎓 GradeFlow — Student Grade & GPA Tracker

A polished **Python web dashboard** for tracking university/college courses, recording assessment scores, calculating weighted averages, and estimating a credit-weighted GPA.

Built as an **independent portfolio project** to demonstrate Python, data validation, database persistence, unit testing, and interactive application development.

## ✨ Features

- **Course manager** — Add, edit, and delete courses with course codes, terms, and credit values.
- **Assessment tracker** — Record quizzes, labs, exams, and projects with scores and percentage weights; edit or remove them at any time.
- **Accurate weighted averages** — See a *current* average calculated from only graded assessments. The app does not call a grade final until the weights total **100%**.
- **Estimated GPA** — Illustrative 4.0-scale credit-weighted GPA using **completed courses only**.
- **Interactive dashboard** — Summary metrics, course progress bars, term filtering, and performance charts.
- **Persistent storage** — SQLite database automatically saved on your machine (`data/gradeflow.sqlite3`).
- **CSV exports** — Download course summaries and individual assessment records.
- **Demo mode** — Generate synthetic sample courses so you can test the application without entering personal grades.
- **Tests** — Built-in `unittest` suite covering grade logic, input validation, and database actions.

## 🛠 Tech stack

- **Python 3.10+** — Core application and business logic
- **Streamlit** — Interactive web user interface
- **SQLite** — Local data persistence via the Python standard library
- **Pandas** — Data display and charts (installed automatically with Streamlit)
- **unittest** — Unit and integration tests

## 🚀 Run locally (macOS / Linux)

Open a terminal in this project folder and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit normally opens a tab at **http://localhost:8501**.

To stop the app, press **Ctrl + C** in the terminal.

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 🧪 Run tests

The calculation and database modules use the **Python standard library**, so tests work *even before* you install Streamlit:

```bash
python3 -m unittest discover -s tests -v
```

## 👩‍💻 How to use

1. Open the **Overview** tab and click **Load example courses** (optional) to try sample data.
2. Open **Courses & grades** to add your own course code, name, term, and credits.
3. Select a course and record assessments with a **score out of 100** and a **course weight**, e.g., `Midterm: 82%, Weight: 30%`.
4. Review your weighted average and the percentage of the course graded so far.
5. The **Insights** tab shows a chart and breakdown of your courses.
6. Use **Export & settings** to save your records as CSV.

### Example weighted average

| Assessment | Score | Course weight | Contribution |
|---|---:|---:|---:|
| Quiz | 80% | 20% | 16 points |
| Midterm | 90% | 30% | 27 points |
| **Total graded** | | **50%** | **43 points** |

The **current average** is `43 / 50 × 100 = 86%`. The app correctly shows **50% remaining** and does **not** treat 86% as a final course grade.

## ⚠️ GPA scale disclaimer

The bundled conversion is an **illustrative US-style 4.0 GPA scale**, not the official grading policy of Seneca Polytechnic or any other specific school. It is suitable for demonstration but **must not be used as an official GPA calculation**.

The app awards GPA points only to courses with a complete set of assessments totalling 100%. The points are credit-weighted:

`estimated GPA = Σ(course grade points × course credits) / Σ(completed course credits)`

To adapt to a school's published rules, edit `GPA_SCALE` in [`tracker.py`](tracker.py). This is a coding exercise, not a guarantee of official accuracy.

## 📁 Project structure

```text
student-grade-gpa-tracker/
├── app.py                  # Interactive Streamlit UI
├── database.py             # CRUD and SQLite data storage
├── tracker.py              # Grade calculations and GPA scale
├── requirements.txt        # Streamlit dependency
├── .streamlit/
│   └── config.toml         # Theme settings
├── tests/
│   ├── test_tracker.py     # Unit tests
│   └── test_database.py    # SQLite integration tests
├── .gitignore              # Prevents committing private grade data
├── LICENSE                 # MIT license
└── README.md               # Documentation
```

## 🔒 Privacy

This is a **local, single-user app** with no login system, web authentication, or cloud database. Grade records live in `data/gradeflow.sqlite3` and the entire `data/` folder is Git-ignored. Avoid putting real personal grades in screenshots or GitHub commits. **Do not deploy this publicly with real student records** without adding access controls and a privacy review.

## 💡 What this project demonstrates

- Separation of concerns across presentation, calculation, and persistence layers
- Structured data storage and parameterized SQL queries
- Validation of invalid scores, weights, duplicates, and missing inputs
- Handling incomplete versus finalized academic data correctly
- Interactive data visualization and CSV export
- Automated testing using temporary databases

## Next improvements

- Import assessments from CSV with validation
- Support user-configurable GPA scales through the UI
- Add optional login and multi-user database support
- Visualize trends across academic terms

---

**Project:** GradeFlow | Python Student Grade & GPA Tracker  
**Purpose:** Learning and software developer portfolio demonstration
