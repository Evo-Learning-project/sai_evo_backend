UPDATE_COURSE = "update_course"
ACCESS_EXERCISES = "access_exercises"
CREATE_EXERCISES = "create_exercises"
MODIFY_EXERCISES = "modify_exercises"
ASSESS_PARTICIPATIONS = "assess_paricipations"
CREATE_EVENTS = "create_events"
UPDATE_EVENTS = "update_events"

TEACHER_PRIVILEGES = [
    UPDATE_COURSE,
    ACCESS_EXERCISES,  # list/retrieve
    CREATE_EXERCISES,
    MODIFY_EXERCISES,  # update/delete
    ASSESS_PARTICIPATIONS,
    CREATE_EVENTS,
    UPDATE_EVENTS,
    "__all__",
]


def check_privileges(user, course, privilege):
    """
    Returns True if and only `user` has `privilege` for `course`
    `course` can either be a Course object or the id of a course
    """
    from courses.models import Course, CoursePrivilege

    if not isinstance(course, Course):
        course = Course.objects.get(pk=course)

    if user == course.creator:
        return True

    try:
        privileges = CoursePrivilege.objects.get(user=user, course=course).privileges
    except CoursePrivilege.DoesNotExist:
        return False

    return "__all__" in privileges or privilege in privileges
