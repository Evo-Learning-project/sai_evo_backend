from rest_framework import filters, mixins, status, viewsets
from courses.models import Course

from gamification.models import GamificationContext
from django.contrib.contenttypes.models import ContentType

from gamification.serializers import GamificationContextSerializer


class CourseGamificationContextViewSet(viewsets.ModelViewSet):
    serializer_class = GamificationContextSerializer
    queryset = GamificationContext.objects.filter(
        content_type=ContentType.objects.get_for_model(Course)
    )
    permission_classes = []
