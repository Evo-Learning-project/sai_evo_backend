from courses.models import Course, Event, EventParticipation, UserCourseEnrollment
from integrations.classroom.integration import GoogleClassroomIntegration
from integrations.classroom.models import GoogleClassroomCourseTwin
from integrations.classroom.tasks import (
    import_enrolled_student_from_twin_course,
    run_google_classroom_integration_method,
)
from users.models import User
from celery import group


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

    def import_enrolled_students(self, course: Course):
        """
        Takes the list of students enrolled in the Classroom course associated with
        the given course and creates UserCourseEnrollment objects for each student
        """
        import_enrolled_student_from_twin_course.delay(course.pk)

    def sync_enrolled_students(self, course: Course):
        """
        Enrolls all students in the given course to the corresponding Classroom course
        """
        model_label = f"{UserCourseEnrollment._meta.app_label}.{UserCourseEnrollment._meta.model_name}"
        enrollment_ids = list(
            UserCourseEnrollment.objects.filter(course=course).values_list(
                "pk", flat=True
            )
        )

        job = group(
            run_google_classroom_integration_method.s(
                "on_student_enrolled", enrollment=f"model_{model_label}_{e}"
            )
            for e in enrollment_ids
        )
        job.delay()

    def sync_exam_grades(self, exam: Event, publish: bool):
        """
        Syncs grades for all students who have taken the given exam.

        If `publish` is True, the Classroom coursework submissions will be returned
        and the grades will be published.
        Otherwise, the grades will be set as draftGrade on the submissions but not
        returned or published.
        """
        model_label = f"{EventParticipation._meta.app_label}.{EventParticipation._meta.model_name}"
        participation_ids = list(
            EventParticipation.objects.filter(event=exam).values_list("pk", flat=True)
        )

        method_name = (
            "on_exam_participation_assessment_published"
            if publish
            else "on_exam_participation_assessment_updated"
        )

        job = group(
            run_google_classroom_integration_method.s(
                method_name, participation=f"model_{model_label}_{p}"
            )
            for p in participation_ids
        )
        job.delay()
