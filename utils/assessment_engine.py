"""
Reusable assessment engine. The SAME functions run the assessment whether
one language is missing or several — each language just gets its own call.
"""
from data.questions_data import QUESTIONS


def get_questions(language):
    """Return the question bank for a language (list of dicts with an index id)."""
    questions = QUESTIONS.get(language, [])
    for i, q in enumerate(questions):
        q["id"] = i
    return questions


def score_assessment(language, answers):
    """
    answers: dict {question_id(str or int): selected_option_letter}
    Returns a result dict with score, correctness counts, skill level and
    per-topic weak areas (topics where the candidate got >=50% wrong).
    """
    questions = get_questions(language)
    total = len(questions)
    correct = 0
    topic_stats = {}  # topic -> [correct, total]

    for q in questions:
        qid = str(q["id"])
        topic = q["topic"]
        topic_stats.setdefault(topic, [0, 0])
        topic_stats[topic][1] += 1
        selected = answers.get(qid)
        if selected and selected == q["correct"]:
            correct += 1
            topic_stats[topic][0] += 1

    incorrect = total - correct
    percent = round((correct / total) * 100, 1) if total else 0.0

    if percent < 50:
        level = "Beginner"
    elif percent < 75:
        level = "Intermediate"
    else:
        level = "Advanced"

    weak_areas = [
        topic for topic, (c, t) in topic_stats.items()
        if t > 0 and (c / t) < 0.5
    ]

    return {
        "language": language,
        "total_questions": total,
        "correct_answers": correct,
        "incorrect_answers": incorrect,
        "score_percent": percent,
        "skill_level": level,
        "weak_areas": weak_areas,
        "topic_stats": topic_stats,
    }
