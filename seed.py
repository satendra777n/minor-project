from werkzeug.security import generate_password_hash
from models import (
    db, User, Profile, ProgrammingLanguage, Job, JobRequirement,
    Question, LearningResource,
)
from data.jobs_data import JOB_REQUIREMENTS, ALL_LANGUAGES
from data.questions_data import QUESTIONS
from data.resources_data import LEARNING_RESOURCES


def seed_if_empty():
    if ProgrammingLanguage.query.first():
        return  # already seeded

    # 1. Programming languages
    lang_objs = {}
    for name in ALL_LANGUAGES:
        lang = ProgrammingLanguage(name=name)
        db.session.add(lang)
        lang_objs[name] = lang
    db.session.flush()

    # 2. Jobs + requirements
    for job_title, langs in JOB_REQUIREMENTS.items():
        job = Job(title=job_title)
        db.session.add(job)
        db.session.flush()
        for lang_name in langs:
            db.session.add(JobRequirement(job_id=job.id, language_id=lang_objs[lang_name].id))

    # 3. Questions
    for lang_name, questions in QUESTIONS.items():
        lang = lang_objs.get(lang_name)
        if not lang:
            continue
        for q in questions:
            db.session.add(Question(
                language_id=lang.id,
                topic=q["topic"],
                q_type=q["q_type"],
                prompt=q["prompt"],
                option_a=q["options"]["a"],
                option_b=q["options"]["b"],
                option_c=q["options"]["c"],
                option_d=q["options"]["d"],
                correct_option=q["correct"],
            ))

    # 4. Learning resources
    for (lang_name, topic), resources in LEARNING_RESOURCES.items():
        lang = lang_objs.get(lang_name)
        if not lang:
            continue
        for r in resources:
            db.session.add(LearningResource(
                language_id=lang.id, topic=topic,
                platform=r["platform"], url=r["url"],
            ))

    # 5. Demo candidate (per project spec: JavaScript on resume, targeting
    #    Full Stack Developer, so Python & SQL come out as missing)
    demo = User(
        name="Demo Candidate",
        email="demo@careergps.com",
        password_hash=generate_password_hash("demo1234"),
    )
    db.session.add(demo)
    db.session.flush()
    db.session.add(Profile(
        user_id=demo.id,
        education="MCA, Final Year",
        skills="JavaScript",
        experience="Academic projects and internship in web development",
    ))

    db.session.commit()
