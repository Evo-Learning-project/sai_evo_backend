from courses.models import Course, UserCourseEnrollment
from integrations.classroom.integration import GoogleClassroomIntegration
from integrations.classroom.models import GoogleClassroomCourseTwin
from integrations.classroom.tasks import bulk_run_google_classroom_integration_method
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
        twin_course = GoogleClassroomCourseTwin.create_from_remote_object(
            course_id=course_id,
            fallback_user=requesting_user,
            remote_object_id=classroom_course_id,
            remote_object=classroom_course,
        )
        return twin_course

    def sync_enrolled_students(self, course: Course):
        """
        Enrolls all students in the given course to the corresponding Classroom course
        """
        twin_course = GoogleClassroomCourseTwin.objects.get(course_id=course.pk)

        model_label = f"{UserCourseEnrollment._meta.app_label}.{UserCourseEnrollment._meta.model_name}"
        enrollments = list(
            UserCourseEnrollment.objects.filter(course=course).values_list(
                "pk", flat=True
            )
        )

        # dispatch the on_student_enrolled action for all enrolled students
        bulk_run_google_classroom_integration_method.delay(
            "on_student_enrolled", model_label, enrollments
        )
