import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import (
    db, User, Profile, Resume, Job, ProgrammingLanguage, JobRequirement,
    SkillGap, Assessment, AssessmentResult, WeakArea, Reassessment, Progress,
)
from data.jobs_data import JOB_REQUIREMENTS
from utils.resume_parser import extract_text, detect_skills
from utils.skill_matcher import compute_skill_gap
from utils.assessment_engine import get_questions, score_assessment
from utils.recommender import get_recommendations
from seed import seed_if_empty

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "career-gps-dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database", "career_gps.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)

db.init_app(app)


# ---------- helpers ----------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def get_or_create_progress(user_id, stage=None):
    prog = Progress.query.filter_by(user_id=user_id).first()
    if not prog:
        prog = Progress(user_id=user_id, stage=stage or "resume_analysis")
        db.session.add(prog)
    elif stage:
        prog.stage = stage
    db.session.commit()
    return prog


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Part 1: onboarding ----------
@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("register"))

        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.flush()
        db.session.add(Profile(user_id=user.id))
        db.session.commit()

        session["user_id"] = user.id
        flash("Account created! Let's build your profile.", "success")
        return redirect(url_for("profile"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(url_for("profile"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/demo-login")
def demo_login():
    """One-click login as the seeded demo candidate, for quick evaluation."""
    demo = User.query.filter_by(email="demo@careergps.com").first()
    if demo:
        session["user_id"] = demo.id
        flash("Logged in as Demo Candidate.", "success")
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("landing"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    prof = user.profile or Profile(user_id=user.id)
    if request.method == "POST":
        prof.education = request.form.get("education", "").strip()
        prof.skills = request.form.get("skills", "").strip()
        prof.experience = request.form.get("experience", "").strip()
        db.session.add(prof)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("resume_upload"))
    return render_template("profile.html", user=user, profile=prof)


@app.route("/resume/upload", methods=["GET", "POST"])
@login_required
def resume_upload():
    user = current_user()
    if request.method == "POST":
        file = request.files.get("resume")
        if not file or file.filename == "":
            flash("Please choose a PDF or DOCX file.", "danger")
            return redirect(url_for("resume_upload"))
        if not allowed_file(file.filename):
            flash("Only PDF and DOCX files are supported.", "danger")
            return redirect(url_for("resume_upload"))

        filename = secure_filename(f"{user.id}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        text = extract_text(filepath)
        skills_found = detect_skills(text)

        resume = Resume(
            user_id=user.id, filename=filename,
            extracted_text=text[:5000],
            extracted_skills=", ".join(skills_found),
        )
        db.session.add(resume)

        # merge resume skills into profile skills (union, de-duplicated)
        prof = user.profile or Profile(user_id=user.id)
        existing = {s.strip() for s in (prof.skills or "").split(",") if s.strip()}
        merged = sorted(existing.union(skills_found))
        prof.skills = ", ".join(merged)
        db.session.add(prof)
        db.session.commit()

        get_or_create_progress(user.id, "resume_analysis")
        return redirect(url_for("resume_analysis"))
    return render_template("resume_upload.html")


@app.route("/resume/analysis")
@login_required
def resume_analysis():
    user = current_user()
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.id.desc()).first()
    return render_template("resume_analysis.html", user=user, resume=resume, profile=user.profile)


@app.route("/target-job", methods=["GET", "POST"])
@login_required
def target_job():
    user = current_user()
    jobs = list(JOB_REQUIREMENTS.keys())
    if request.method == "POST":
        job_title = request.form.get("job_title")
        if job_title not in JOB_REQUIREMENTS:
            flash("Please select a valid target job.", "danger")
            return redirect(url_for("target_job"))

        job = Job.query.filter_by(title=job_title).first()
        prof = user.profile
        prof.target_job_id = job.id if job else None
        db.session.commit()

        candidate_skills = [s.strip() for s in (prof.skills or "").split(",") if s.strip()]
        gap = compute_skill_gap(candidate_skills, job_title)

        skill_gap = SkillGap(
            user_id=user.id, job_id=job.id,
            matched=", ".join(gap["matched"]),
            missing=", ".join(gap["missing"]),
            weak=", ".join(gap["weak"]),
        )
        db.session.add(skill_gap)
        get_or_create_progress(user.id, "skill_gap")
        db.session.commit()
        return redirect(url_for("skill_gap_dashboard"))
    return render_template("target_job.html", jobs=jobs)


# ---------- Part 2: skill gap + assessment ----------
@app.route("/skill-gap")
@login_required
def skill_gap_dashboard():
    user = current_user()
    gap = SkillGap.query.filter_by(user_id=user.id).order_by(SkillGap.id.desc()).first()
    if not gap:
        flash("Select a target job first to see your skill gap.", "info")
        return redirect(url_for("target_job"))
    return render_template("skill_gap.html", gap=gap, job=gap.job)


@app.route("/missing-languages")
@login_required
def missing_languages():
    user = current_user()
    gap = SkillGap.query.filter_by(user_id=user.id).order_by(SkillGap.id.desc()).first()
    if not gap:
        return redirect(url_for("target_job"))
    missing = [l.strip() for l in (gap.missing or "").split(",") if l.strip()]
    weak = [l.strip() for l in (gap.weak or "").split(",") if l.strip()]

    # latest score per language, if already assessed
    latest_scores = {}
    for lang_name in missing + weak:
        result = (AssessmentResult.query.join(ProgrammingLanguage)
                  .filter(AssessmentResult.user_id == user.id,
                          ProgrammingLanguage.name == lang_name)
                  .order_by(AssessmentResult.id.desc()).first())
        if result:
            latest_scores[lang_name] = result

    return render_template("missing_language.html", missing=missing, weak=weak,
                            latest_scores=latest_scores)


@app.route("/assessment/<language>", methods=["GET", "POST"])
@login_required
def assessment(language):
    user = current_user()
    questions = get_questions(language)
    if not questions:
        flash(f"No assessment is available yet for {language}.", "warning")
        return redirect(url_for("missing_languages"))

    if request.method == "POST":
        answers = {qid.replace("q_", ""): val for qid, val in request.form.items() if qid.startswith("q_")}
        result_data = score_assessment(language, answers)

        lang_obj = ProgrammingLanguage.query.filter_by(name=language).first()
        assess = Assessment(user_id=user.id, language_id=lang_obj.id, attempt_number=1)
        db.session.add(assess)
        db.session.flush()

        result = AssessmentResult(
            assessment_id=assess.id, user_id=user.id, language_id=lang_obj.id,
            total_questions=result_data["total_questions"],
            correct_answers=result_data["correct_answers"],
            incorrect_answers=result_data["incorrect_answers"],
            score_percent=result_data["score_percent"],
            skill_level=result_data["skill_level"],
            attempt_number=1,
        )
        db.session.add(result)
        db.session.flush()
        for topic in result_data["weak_areas"]:
            db.session.add(WeakArea(result_id=result.id, topic=topic))
        db.session.commit()

        get_or_create_progress(user.id, "programming_assessment")
        return redirect(url_for("assessment_result", result_id=result.id))

    return render_template("assessment.html", language=language, questions=questions)


@app.route("/assessment/result/<int:result_id>")
@login_required
def assessment_result(result_id):
    result = AssessmentResult.query.get_or_404(result_id)
    weak_topics = [w.topic for w in result.weak_areas]
    return render_template("assessment_result.html", result=result, weak_topics=weak_topics)


# ---------- Part 3: learning + reassessment ----------
@app.route("/learning/<language>")
@login_required
def learning_recommendations(language):
    user = current_user()
    result = (AssessmentResult.query.join(ProgrammingLanguage)
              .filter(AssessmentResult.user_id == user.id, ProgrammingLanguage.name == language)
              .order_by(AssessmentResult.id.desc()).first())
    weak_topics = [w.topic for w in result.weak_areas] if result else []
    recommendations = get_recommendations(language, weak_topics)
    return render_template("learning_recommendations.html", language=language,
                            result=result, recommendations=recommendations)


@app.route("/reassessment/<language>", methods=["GET", "POST"])
@login_required
def reassessment(language):
    user = current_user()
    questions = get_questions(language)
    lang_obj = ProgrammingLanguage.query.filter_by(name=language).first()

    previous = (AssessmentResult.query.filter_by(user_id=user.id, language_id=lang_obj.id)
                .order_by(AssessmentResult.id.desc()).first())
    if not previous:
        flash("Take the initial assessment before reassessing.", "warning")
        return redirect(url_for("assessment", language=language))

    if request.method == "POST":
        answers = {qid.replace("q_", ""): val for qid, val in request.form.items() if qid.startswith("q_")}
        result_data = score_assessment(language, answers)
        next_attempt = previous.attempt_number + 1

        assess = Assessment(user_id=user.id, language_id=lang_obj.id, attempt_number=next_attempt)
        db.session.add(assess)
        db.session.flush()

        new_result = AssessmentResult(
            assessment_id=assess.id, user_id=user.id, language_id=lang_obj.id,
            total_questions=result_data["total_questions"],
            correct_answers=result_data["correct_answers"],
            incorrect_answers=result_data["incorrect_answers"],
            score_percent=result_data["score_percent"],
            skill_level=result_data["skill_level"],
            attempt_number=next_attempt,
        )
        db.session.add(new_result)
        db.session.flush()
        for topic in result_data["weak_areas"]:
            db.session.add(WeakArea(result_id=new_result.id, topic=topic))

        improvement = round(result_data["score_percent"] - previous.score_percent, 1)
        reassess = Reassessment(
            user_id=user.id, language_id=lang_obj.id,
            before_score=previous.score_percent,
            after_score=result_data["score_percent"],
            improvement=improvement,
        )
        db.session.add(reassess)
        get_or_create_progress(user.id, "reassessment")
        db.session.commit()
        return redirect(url_for("reassessment_result", reassessment_id=reassess.id))

    return render_template("assessment.html", language=language, questions=questions, is_reassessment=True)


@app.route("/reassessment/result/<int:reassessment_id>")
@login_required
def reassessment_result(reassessment_id):
    reassess = Reassessment.query.get_or_404(reassessment_id)
    return render_template("reassessment_result.html", reassess=reassess)


# ---------- Part 4: dashboards ----------
@app.route("/progress")
@login_required
def progress_dashboard():
    user = current_user()
    reassessments = Reassessment.query.filter_by(user_id=user.id).order_by(Reassessment.id).all()
    all_results = (AssessmentResult.query.filter_by(user_id=user.id)
                   .order_by(AssessmentResult.language_id, AssessmentResult.attempt_number).all())
    return render_template("progress_dashboard.html", reassessments=reassessments, results=all_results)


@app.route("/readiness")
@login_required
def readiness_dashboard():
    user = current_user()
    gap = SkillGap.query.filter_by(user_id=user.id).order_by(SkillGap.id.desc()).first()
    if not gap:
        flash("Complete the skill gap analysis first.", "info")
        return redirect(url_for("target_job"))

    matched = [l.strip() for l in (gap.matched or "").split(",") if l.strip()]
    missing = [l.strip() for l in (gap.missing or "").split(",") if l.strip()]
    weak = [l.strip() for l in (gap.weak or "").split(",") if l.strip()]
    required = matched + missing + weak

    per_language = []
    total_score = 0
    for lang_name in required:
        latest = (AssessmentResult.query.join(ProgrammingLanguage)
                  .filter(AssessmentResult.user_id == user.id, ProgrammingLanguage.name == lang_name)
                  .order_by(AssessmentResult.id.desc()).first())
        score = latest.score_percent if latest else (100.0 if lang_name in matched else 0.0)
        total_score += score
        per_language.append({
            "language": lang_name,
            "score": score,
            "level": latest.skill_level if latest else ("Advanced" if lang_name in matched else "Not assessed"),
            "weak_areas": [w.topic for w in latest.weak_areas] if latest else [],
        })

    overall_readiness = round(total_score / len(required), 1) if required else 0.0

    prog = get_or_create_progress(user.id, "career_readiness")
    prog.overall_readiness = overall_readiness
    db.session.commit()

    return render_template("readiness_dashboard.html", job=gap.job, matched=matched,
                            missing=missing, weak=weak, per_language=per_language,
                            overall_readiness=overall_readiness)


with app.app_context():
    db.create_all()
    seed_if_empty()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
