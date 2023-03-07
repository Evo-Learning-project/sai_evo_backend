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
                "course",
                "classroom_courses",
            ],  # TODO ! move "course" and "classroom_courses" to separate rule
            "principal": ["authenticated"],
            "effect": "allow",
        },
    ]
