from django.core.exceptions import ValidationError

UPDATE_COURSE = "update_course"
ACCESS_EXERCISES = "access_exercises"
MANAGE_EXERCISES = "manage_exercises"
ASSESS_PARTICIPATIONS = "assess_participations"
MANAGE_EVENTS = "manage_events"
MANAGE_EXERCISE_SOLUTIONS = "manage_exercise_solutions"

TEACHER_PRIVILEGES = [
    UPDATE_COURSE,
    ACCESS_EXERCISES,  # list/retrieve
    MANAGE_EXERCISES,
    ASSESS_PARTICIPATIONS,
    MANAGE_EVENTS,
    MANAGE_EXERCISE_SOLUTIONS,
]


import logging

logger = logging.getLogger(__name__)


def validate_permission_list(lst):
    if not isinstance(lst, list):
        raise ValidationError("Privileges field must be a list")

    for item in lst:
        if not isinstance(item, str):
            raise ValidationError("Privileges must be strings")
        if item not in TEACHER_PRIVILEGES:
            raise ValidationError(f"{item} not in teacher privileges")


def get_user_privileges(user, course):
    from courses.models import Course, UserCoursePrivilege

    if user.is_anonymous:
        return []

    if not isinstance(course, Course):
        # TODO handle exceptions
        course = Course.objects.get(pk=course)

    if user == course.creator:
        return TEACHER_PRIVILEGES

    # if data has been prefetched, use the optimized data
    if hasattr(user, "prefetched_course_roles"):
        user_roles = [
            r for r in user.prefetched_course_roles if r.course.pk == course.pk
        ]
    elif hasattr(course, "prefetched_user_roles"):
        user_roles = [r for r in course.prefetched_user_roles if r.user.pk == user.pk]
    else:
        user_roles = user.roles.filter(course=course)

    allow_privileges = [
        privilege
        for role_privileges in (role.allow_privileges for role in user_roles)
        for privilege in role_privileges
    ]

    try:
        # if data has been prefetched, use the optimized data
        if hasattr(user, "prefetched_privileged_courses"):
            per_user_privileges = [
                c
                for c in user.prefetched_privileged_courses
                if c.course.pk == course.pk
            ][0]
        elif hasattr(course, "prefetched_privileged_users"):
            per_user_privileges = [
                u for u in course.prefetched_privileged_users if u.user.pk == user.pk
            ][0]
        else:
            # !!
            per_user_privileges = UserCoursePrivilege.objects.get(
                user=user, course=course
            )

        allow_privileges.extend(per_user_privileges.allow_privileges)  # add per-user
        deny_privileges = per_user_privileges.deny_privileges
    except (UserCoursePrivilege.DoesNotExist, IndexError):
        deny_privileges = []

    return [
        privilege for privilege in allow_privileges if privilege not in deny_privileges
    ]


def check_privilege(user, course, privilege):
    """
    Returns True if and only `user` has `privilege` for `course`
    `course` can either be a Course object or the id of a course
    """
    # !!
    privileges = get_user_privileges(user, course)

    if privilege == "__some__":
        return len(privileges) > 0

    return "__all__" in privileges or privilege in privileges
