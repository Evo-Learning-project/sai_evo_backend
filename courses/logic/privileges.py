UPDATE_COURSE = "update_course"
ACCESS_EXERCISES = "access_exercises"
CREATE_EXERCISES = "create_exercises"
MODIFY_EXERCISES = "modify_exercises"
# ACCESS_PARTICIPATIONS = "access_paricipations"
ASSESS_PARTICIPATIONS = "assess_paricipations"
CREATE_EVENTS = "create_events"
UPDATE_EVENTS = "update_events"

TEACHER_PRIVILEGES = [
    UPDATE_COURSE,
    ACCESS_EXERCISES,  # list/retrieve
    CREATE_EXERCISES,
    MODIFY_EXERCISES,  # update/delete
    # ACCESS_PARTICIPATIONS,  # list/retrieve
    ASSESS_PARTICIPATIONS,
    CREATE_EVENTS,
    UPDATE_EVENTS,
    "__all__",
]


def check_privileges(user, course, privilege):
    from courses.models import Course, CoursePrivilege

    if user == course.creator:
        return True

    if isinstance(course, Course):
        course_kwarg = {"course": course}
    else:
        course_kwarg = {"course_id": course}

    try:
        privileges = CoursePrivilege.objects.get(user=user, **course_kwarg).privileges
    except CoursePrivilege.DoesNotExist:
        return False

    return "__all__" in privileges or privilege in privileges
