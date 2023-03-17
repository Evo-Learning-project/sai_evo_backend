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
                "classroom_courses",
            ],  # TODO ---
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]
