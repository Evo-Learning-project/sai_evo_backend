from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from courses.models import Course, Event

from integrations.classroom import auth
from django.conf import settings

from social_core.backends.google import GoogleOAuth2

from django.shortcuts import get_object_or_404


import logging
from integrations.classroom.controller import GoogleClassroomIntegrationController
from integrations.classroom.exceptions import (
    InvalidGoogleOAuth2Credentials,
    MissingGoogleOAuth2Credentials,
)
from integrations.classroom.integration import GoogleClassroomIntegration
from integrations.classroom.models import (
    GoogleClassroomAnnouncementTwin,
    GoogleClassroomCourseTwin,
    GoogleClassroomCourseWorkTwin,
    GoogleClassroomMaterialTwin,
)
from integrations.classroom.serializers import (
    GoogleClassroomAnnouncementTwinSerializer,
    GoogleClassroomCourseTwinSerializer,
    GoogleClassroomCourseWorkTwinSerializer,
    GoogleClassroomMaterialTwinSerializer,
)

from integrations.models import GoogleOAuth2Credentials
from integrations.classroom import policies
from users.models import User

from rest_framework.renderers import StaticHTMLRenderer, JSONRenderer


logger = logging.getLogger(__name__)


class GoogleClassroomViewSet(viewsets.ViewSet):
    permission_classes = [policies.GoogleClassroomAccessPolicy]

    def get_renderers(self):
        if self.action == "oauth2_callback":
            return [StaticHTMLRenderer()]
        return super().get_renderers()

    # TODO verify if only "get" is sufficient
    @action(methods=["get", "post", "put"], detail=False)
    def oauth2_callback(self, request, *args, **kwargs):
        """
        Callback view that gets called by Google upon the user completing the
        authentication flow. This view is specifically used for incremental auth
        and will be called when the user grants additional permissions in order
        to allow Evo access to Google Classroom resources owned by the user
        """

        request_url = settings.BASE_BACKEND_URL + request.get_full_path()

        flow = auth.get_flow(scope_role=None)

        try:
            response = flow.fetch_token(authorization_response=request_url)
            # use returned token to fetch user profile and determine whom
            # to associate the credentials to
            user_profile = GoogleOAuth2().user_data(
                access_token=response["access_token"]
            )
        except Exception as e:
            logger.exception("Google OAuth callback failed to fetch token", exc_info=e)
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            email = user_profile.get("email", "")
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.critical(
                "Google OAuth callback failed to find user with email " + str(email)
            )
            return Response(status=status.HTTP_404_NOT_FOUND)

        # create credentials object and associate it to user
        GoogleOAuth2Credentials.create_from_auth_response(user, response)

        # this view will be reached directly by the user's browser since
        # it'll be accessed through the redirect_uri param of google oauth.
        # return a response with a script that closes the page
        return Response(
            """
                        <html>
                            <body>Success!</body>
                            <script type="text/javascript">
                                window.close();
                            </script>
                        </html>
            """
        )

    @action(methods=["get"], detail=False)
    def authorized_scopes(self, request, *args, **kwargs):
        try:
            creds = GoogleClassroomIntegration().get_credentials(user=request.user)
            scopes = creds.scopes
        except MissingGoogleOAuth2Credentials:
            scopes = []
        except InvalidGoogleOAuth2Credentials:
            logger.critical("Invalid credentials for user " + str(request.user.pk))
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(data=scopes, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def auth_url(self, request, *args, **kwargs):
        role = request.query_params.get("role")
        if role not in ["teacher", "student"]:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        url = auth.get_auth_request_url(user=request.user, scope_role=role)
        return Response(data=url, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def classroom_courses(self, request, *args, **kwargs):
        """
        Returns a list of Google Classroom courses for which the requesting
        user is a teacher
        """
        # TODO handle errors
        courses = GoogleClassroomIntegration().get_courses_taught_by(request.user)
        return Response(data=courses, status=status.HTTP_200_OK)

    @action(methods=["get", "patch", "post"], detail=False)
    def course(self, request, *args, **kwargs):
        """
        Allow retrieving, creating, enabling, and disabling a twin course
        for the given course. This view is used to pair an Evo course with
        a Classroom course, to look up that relation, and to enable or disable
        it. A query param named `course_id` is mandatory.
        """
        # TODO review
        course_id = request.query_params.get("course_id")
        if course_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if request.method == "POST":
            classroom_course_id = request.data.get("classroom_course_id")
            if classroom_course_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            # create a new twin course
            twin_course = GoogleClassroomIntegrationController().associate_evo_course_to_classroom_course(
                requesting_user=request.user,
                course_id=course_id,
                classroom_course_id=classroom_course_id,
            )
            data = GoogleClassroomCourseTwinSerializer(twin_course).data
            return Response(data, status=status.HTTP_201_CREATED)

        twin_course = get_object_or_404(
            GoogleClassroomCourseTwin.objects.all(), course_id=course_id
        )
        if request.method == "GET":
            data = GoogleClassroomCourseTwinSerializer(twin_course).data
            return Response(data, status=status.HTTP_200_OK)
        elif request.method == "PATCH":
            serializer = GoogleClassroomCourseTwinSerializer(
                twin_course,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            assert False

    # TODO refactor shared code among the three actions below

    @action(methods=["get"], detail=False)
    def coursework(self, request, *args, **kwargs):
        """
        Allows retrieving a Classroom coursework item associated with the given Evo Event
        """
        event_id = request.query_params.get("event_id")
        if event_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        coursework = get_object_or_404(
            GoogleClassroomCourseWorkTwin.objects.all(), event_id=event_id
        )
        data = GoogleClassroomCourseWorkTwinSerializer(coursework).data
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def material(self, request, *args, **kwargs):
        """
        Allows retrieving a Classroom material item associated
        with the given Evo LessonNode
        """
        lesson_id = request.query_params.get("lesson_id")
        if lesson_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        material = get_object_or_404(
            GoogleClassroomMaterialTwin.objects.all(), lesson_id=lesson_id
        )
        data = GoogleClassroomMaterialTwinSerializer(material).data
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def announcement(self, request, *args, **kwargs):
        """
        Allows retrieving a Classroom material item associated
        with the given Evo LessonNode
        """
        announcement_id = request.query_params.get("announcement_id")
        if announcement_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        announcement = get_object_or_404(
            GoogleClassroomAnnouncementTwin.objects.all(),
            announcement_id=announcement_id,
        )
        data = GoogleClassroomAnnouncementTwinSerializer(announcement).data
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=False)
    def sync_exam_grades(self, request, *args, **kwargs):
        event_id = request.query_params.get("event_id")
        if event_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event = get_object_or_404(Event.objects.all(), pk=event_id)

        # TODO create some model to store the status of the task
        GoogleClassroomIntegrationController().sync_exam_grades(
            exam=event, publish=False
        )

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(methods=["post"], detail=False)
    def sync_course_roster(self, request, *args, **kwargs):
        course_id = request.query_params.get("course_id")
        if course_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course.objects.all(), pk=course_id)
        GoogleClassroomIntegrationController().import_enrolled_students(course=course)

        return Response(status=status.HTTP_202_ACCEPTED)
