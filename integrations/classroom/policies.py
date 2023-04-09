from rest_access_policy import AccessPolicy


class GoogleClassroomAccessPolicy(AccessPolicy):
    statements = [
        {
            "action": ["oauth2_callback"],
            "principal": ["*"],
            "effect": "allow",
        },
        {
            "action": [
                "authorized_scopes",
                "auth_url",
                # TODO create specific rules for all the entries below
                "course",
                "coursework",
                "announcement",
                "material",
                "classroom_courses",
                "sync_exam_grades",
            ],  # TODO ---
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]
