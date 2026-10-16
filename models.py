from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("Profile", backref="user", uselist=False)
    resumes = db.relationship("Resume", backref="user")
    skill_gaps = db.relationship("SkillGap", backref="user")
    assessment_results = db.relationship("AssessmentResult", backref="user")
    reassessments = db.relationship("Reassessment", backref="user")
    progress = db.relationship("Progress", backref="user", uselist=False)


class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    education = db.Column(db.String(255))
    skills = db.Column(db.String(500))  # comma separated
    experience = db.Column(db.String(500))
    target_job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"))


class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255))
    extracted_text = db.Column(db.Text)
    extracted_skills = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class ProgrammingLanguage(db.Model):
    __tablename__ = "programming_languages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=True, nullable=False)
    requirements = db.relationship("JobRequirement", backref="job")


class JobRequirement(db.Model):
    __tablename__ = "job_requirements"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("programming_languages.id"), nullable=False)
    language = db.relationship("ProgrammingLanguage")


class SkillGap(db.Model):
    __tablename__ = "skill_gaps"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    matched = db.Column(db.String(500))
    missing = db.Column(db.String(500))
    weak = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    job = db.relationship("Job")


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("programming_languages.id"), nullable=False)
    topic = db.Column(db.String(80), nullable=False)
    q_type = db.Column(db.String(30), default="mcq")  # mcq / output / practical
    prompt = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255))
    option_b = db.Column(db.String(255))
    option_c = db.Column(db.String(255))
    option_d = db.Column(db.String(255))
    correct_option = db.Column(db.String(1))  # a/b/c/d
    language = db.relationship("ProgrammingLanguage")


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("programming_languages.id"), nullable=False)
    attempt_number = db.Column(db.Integer, default=1)  # 1 = initial, 2+ = reassessment
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.relationship("ProgrammingLanguage")


class AssessmentResult(db.Model):
    __tablename__ = "assessment_results"
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessments.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("programming_languages.id"), nullable=False)
    total_questions = db.Column(db.Integer)
    correct_answers = db.Column(db.Integer)
    incorrect_answers = db.Column(db.Integer)
    score_percent = db.Column(db.Float)
    skill_level = db.Column(db.String(20))
    attempt_number = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.relationship("ProgrammingLanguage")
    weak_areas = db.relationship("WeakArea", backref="result")


class WeakArea(db.Model):
    __tablename__ = "weak_areas"
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey("assessment_results.id"), nullable=False)
    topic = db.Column(db.String(80), nullable=False)


class LearningResource(db.Model):
    __tablename__ = "learning_resources"
    id = db.Column(db.Integer, primary_key=True)
    language_id = db.Column(db.Integer, db.ForeignKey("programming_languages.id"), nullable=False)
    topic = db.Column(db.String(80), nullable=False)
    platform = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    language = db.relationship("ProgrammingLanguage")


class Reassessment(db.Model):
    __tablename__ = "reassessments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    language_id = db.Column(db.Integer, db.ForeignKey("programming_languages.id"), nullable=False)
    before_score = db.Column(db.Float)
    after_score = db.Column(db.Float)
    improvement = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.relationship("ProgrammingLanguage")


class Progress(db.Model):
    __tablename__ = "progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    stage = db.Column(db.String(50), default="resume_analysis")
    overall_readiness = db.Column(db.Float, default=0.0)
