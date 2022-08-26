from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from gamification import views

# `/gamification` entry point
router = routers.SimpleRouter()

router.register(
    r"",
    views.CourseGamificationContextViewSet,
    basename="gamification_contexts",
)


urlpatterns = [
    path("", include(router.urls)),
]
