from demo_mode import views
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

router = routers.SimpleRouter()
router.register(
    r"invitations",
    views.DemoInvitationViewSet,
    basename="invitations",
)
urlpatterns = [
    path("", include(router.urls)),
]
