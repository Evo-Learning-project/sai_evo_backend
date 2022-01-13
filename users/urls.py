from courses import views
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

router = routers.SimpleRouter()
router.register(
    r"",
    views.UserViewSet,
    basename="users",
)
urlpatterns = [
    re_path(r"^auth/", include("drf_social_oauth2.urls", namespace="drf")),
    path("", include(router.urls)),
]
