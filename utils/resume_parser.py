"""
Resume processing module.
Handles PDF/DOCX text extraction and keyword-based skill detection.

This module is intentionally modular: `extract_text()` and `detect_skills()`
are separated so a smarter NLP/embedding-based matcher can be swapped in
later without touching the rest of the application.
"""
import os
import re

try:
    from PyPDF2 import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    import docx
except ImportError:  # pragma: no cover
    docx = None

# Known programming languages / skills the parser looks for in resume text.
KNOWN_SKILLS = [
    "Python", "JavaScript", "Java", "SQL", "C++", "C", "HTML", "CSS",
    "HTML/CSS", "TypeScript", "React", "Flask", "Django", "Node.js",
    "MySQL", "MongoDB", "Git",
]


def extract_text(filepath):
    """Extract raw text from a PDF or DOCX resume file."""
    ext = os.path.splitext(filepath)[1].lower()
    text = ""
    try:
        if ext == ".pdf" and PdfReader is not None:
            reader = PdfReader(filepath)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        elif ext == ".docx" and docx is not None:
            document = docx.Document(filepath)
            text = "\n".join(p.text for p in document.paragraphs)
        else:
            # fallback: plain text read
            with open(filepath, "r", errors="ignore") as f:
                text = f.read()
    except Exception:
        text = ""
    return text


def detect_skills(text):
    """
    Keyword/similarity-based skill detection from resume text.
    Returns a list of matched skill names (from KNOWN_SKILLS) found in the text.

    This is a simple case-insensitive keyword scan today; the function
    boundary is kept clean so it can later be replaced with an NLP/embedding
    based similarity matcher without changing any caller.
    """
    if not text:
        return []
    normalized = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        # handle "HTML/CSS" style compound skill names
        parts = re.split(r"[\/]", skill)
        if any(re.search(r"\b" + re.escape(p.lower()) + r"\b", normalized) for p in parts):
            found.append(skill)
    return found
