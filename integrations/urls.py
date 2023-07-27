from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from course_tree.views import NodeCommentViewSet, PollNodeChoiceViewSet, TreeNodeViewSet
from integrations.classroom import views

# `/courses` entry point
router = routers.SimpleRouter()
router.register(
    r"classroom",
    views.GoogleClassroomViewSet,
    basename="classroom",
)


urlpatterns = [
    path("", include(router.urls)),
]
