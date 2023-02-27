def get_material_payload(title, description):
    return {
        "title": title,
        "description": description,
        "state": "PUBLISHED",
        # "topicId": topicId
    }


def get_announcement_payload(text):
    return {
        "text": text,
        "state": "PUBLISHED",
        "assigneeMode": "ALL_STUDENTS",
    }


def get_assignment_payload(title, description, exam_url):
    return {
        "title": title,
        "description": description,
        "materials": [
            {"link": {"url": exam_url}},
        ],
        "workType": "ASSIGNMENT",
        "state": "PUBLISHED",
    }
