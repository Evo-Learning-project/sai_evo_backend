from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from gamification import views

# `/gamification` entry point
router = routers.SimpleRouter()
router.register(
    r"contexts",
    views.CourseGamificationContextViewSet,
    basename="gamification_contexts",
)

context_router = routers.NestedSimpleRouter(
    router,
    r"contexts",
    lookup="context",
)

# `/contexts/<pk>/goals` entry point
context_router.register(
    r"goals",
    views.GoalViewSet,
    basename="context-goals",
)


urlpatterns = [
    path("", include(router.urls)),
    path("", include(context_router.urls)),
]
