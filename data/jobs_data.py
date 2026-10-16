"""Static mapping of target jobs -> required programming languages.
This is the reference data used to compute skill gaps."""

JOB_REQUIREMENTS = {
    "Full Stack Developer": ["JavaScript", "Python", "SQL"],
    "Python Developer": ["Python", "SQL"],
    "Java Developer": ["Java", "SQL"],
    "Frontend Developer": ["JavaScript", "HTML/CSS"],
    "Backend Developer": ["Python", "SQL", "Java"],
    "Data Analyst": ["Python", "SQL"],
    "Software Developer": ["Java", "Python", "C++"],
}

ALL_LANGUAGES = sorted({lang for langs in JOB_REQUIREMENTS.values() for lang in langs})
