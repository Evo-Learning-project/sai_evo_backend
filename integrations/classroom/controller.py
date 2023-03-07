from courses.models import Course
from integrations.classroom.integration import GoogleClassroomIntegration
from integrations.classroom.models import GoogleClassroomCourseTwin
from users.models import User


class GoogleClassroomIntegrationController:
    """
    A class that handles certain actions that can be performed with regards
    to the Classroom integration, for example associating a course to a Classroom
    course.

    This class combines primitives from `GoogleClassroomIntegration` to
    perform more complex operations. In particular, the controller handles actions
    which involve the creation, deletion, and update of model instances related to
    the Classroom integration, unlike the `GoogleClassroomIntegration` class, which
    is responsible for performing actions that affect the remote Classroom course.
    """

    def associate_evo_course_to_classroom_course(
        self,
        requesting_user: User,
        course_id: str,
        classroom_course_id: str,
    ) -> GoogleClassroomCourseTwin:
        # fetch Google Classroom course using given id
        classroom_course = GoogleClassroomIntegration().get_course_by_id(
            requesting_user,
            classroom_course_id,
        )
        # create a twin resource that links the given course to the
        # specified classroom course
        # TODO handle unique constraint failure
        twin_course = GoogleClassroomCourseTwin(
            course_id=course_id,
            remote_object_id=classroom_course_id,
        )
        twin_course.set_remote_object(classroom_course)
        twin_course.save()

        return twin_course

    def sync_enrolled_students(self, course: Course):
        """
        Retrieves the list of students enrolled in the twin Classroom course
        for the given course, and syncs the students enrolled in the course on
        Evo with the resulting list. This creates enrollments for any students
        that are enrolled in the Classroom twin course and deletes any existing
        enrollments for which there is no corresponding enrollment in the
        Classroom twin course.
        """
        ...
