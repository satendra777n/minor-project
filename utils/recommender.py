"""Maps weak areas to external learning resources. No platform is ranked."""
from data.resources_data import LEARNING_RESOURCES, DEFAULT_RESOURCE


def get_recommendations(language, weak_topics):
    """Returns list of dicts: {topic, platform, url} for each weak topic."""
    recs = []
    for topic in weak_topics:
        resources = LEARNING_RESOURCES.get((language, topic), [DEFAULT_RESOURCE])
        for r in resources:
            recs.append({"topic": topic, "platform": r["platform"], "url": r["url"]})
    return recs
