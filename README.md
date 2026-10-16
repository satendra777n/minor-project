# Career GPS — Personalized Skill Assessment & Career Readiness Platform

Your Personalized Journey from Skills to Career Readiness.

Career GPS is an MCA academic project: a working Flask web app that takes a
candidate's resume + target job, works out which **programming languages**
they're missing, tests their **actual** knowledge of each one, points them to
external learning resources for their weak topics, and then lets them
reassess to measure improvement — ending in a Career Readiness dashboard.

## Tech stack
- **Frontend:** HTML5, CSS3, Bootstrap 5, vanilla JS
- **Backend:** Python, Flask, Flask-SQLAlchemy (REST-style routes)
- **Database:** SQLite (`database/career_gps.db`), schema designed to move to MySQL later
- **Resume parsing:** PyPDF2 (PDF) and python-docx (DOCX)

## Project structure
```
career_gps/
  app.py                  # Flask routes / application entry point
  models.py               # SQLAlchemy models (14 tables)
  seed.py                 # Seeds languages, jobs, questions, resources, demo user
  data/
    jobs_data.py           # Job → required-languages mapping
    questions_data.py       # Assessment question bank, tagged by topic
    resources_data.py       # External learning resource lookup (by language + topic)
  utils/
    resume_parser.py       # PDF/DOCX text extraction + keyword skill detection
    skill_matcher.py        # Matched / Missing / Weak computation
    assessment_engine.py    # Reusable scoring engine (score %, skill level, weak topics)
    recommender.py          # Weak topic → learning resource lookup
  templates/               # 15 Jinja2 pages (see below)
  static/css/style.css     # Blue, card-based professional theme
  static/js/main.js        # Assessment form validation
  static/uploads/          # Uploaded resumes land here
  database/                # SQLite file is created here on first run
```

## Pages
Landing · Register · Login · Candidate Profile · Resume Upload · Resume
Analysis · Target Job Selection · Skill Gap Dashboard · Missing Language
Selection · Programming Language Assessment · Assessment Result ·
Personalized Learning Recommendations · Knowledge Check / Reassessment ·
Progress / Growth Dashboard · Career Readiness Dashboard.

## How it works
1. **Resume + Target Job** — candidate fills a profile, uploads a resume
   (skills are extracted and merged into their profile), then picks a target
   job (e.g. *Full Stack Developer*).
2. **Skill Gap** — `utils/skill_matcher.py` compares profile skills against
   the job's required languages and buckets them into **Matched / Missing /
   Weak**.
3. **Assessment** — for *every* missing (or weak) language, the candidate
   takes a separate 8–10 question test (MCQ, syntax, output-based, practical).
   The same `utils/assessment_engine.py` functions run the test regardless of
   whether one language or several are missing. Scoring produces a
   percentage, a skill level (Beginner / Intermediate / Advanced), and a list
   of weak topics (any topic where <50% of its questions were answered
   correctly).
4. **Learning Recommendations** — weak topics are mapped to external
   resources (freeCodeCamp, Coursera, edX, Codecademy — unranked).
5. **Reassessment** — after studying, the candidate retakes the same
   language's assessment. Before/after scores and the improvement delta are
   stored and shown with progress bars.
6. **Career Readiness Dashboard** — combines target job, matched/missing
   languages, latest scores, weak areas and an overall readiness percentage.

## Setup & run

```bash
cd career_gps
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. The database and demo data are created
automatically on first run — no manual migration step needed.

### Try it instantly
Click **"Try Demo Account"** on the login page (or visit `/demo-login`) to
log in as the seeded demo candidate:
- Target job: Full Stack Developer (requires JavaScript, Python, SQL)
- Resume skill: JavaScript only → Missing: Python, SQL
- You can immediately run a Python or SQL assessment from **Missing
  Languages** to see the full flow.

Or register your own account from `/register` and go through the full
onboarding flow yourself.

## Notes for extending this project
- **NLP-based skill matching:** `utils/resume_parser.detect_skills()` and
  `utils/skill_matcher.compute_skill_gap()` are isolated on purpose. Today
  they use keyword matching; you can swap in embeddings/fuzzy matching
  (e.g. spaCy, sentence-transformers) without touching any route in `app.py`.
- **More languages/jobs:** add entries to `data/jobs_data.py`,
  `data/questions_data.py`, and `data/resources_data.py` — the rest of the
  app (routes, scoring, dashboards) is fully data-driven and needs no code
  changes.
- **MySQL later:** the SQLAlchemy models don't use any SQLite-specific
  features — swap the `SQLALCHEMY_DATABASE_URI` in `app.py` for a MySQL URI
  when you're ready.
