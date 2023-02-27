from django.utils.html import strip_tags


def get_material_payload(title, description, material_url):
    return {
        "title": title,
        "description": description,
        "state": "PUBLISHED",
        "materials": [
            {"link": {"url": material_url}},
        ],
        # "topicId": topicId
    }


def get_announcement_payload(text, announcement_url):
    return {
        "text": strip_tags(text),
        "state": "PUBLISHED",
        "assigneeMode": "ALL_STUDENTS",
        "materials": [
            {"link": {"url": announcement_url}},
        ],
    }


def get_assignment_payload(title, description, exam_url):
    return {
        "title": strip_tags(title),
        "description": strip_tags(description),
        "materials": [
            {"link": {"url": exam_url}},
        ],
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED",
    }
