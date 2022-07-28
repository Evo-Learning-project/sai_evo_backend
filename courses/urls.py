from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from courses import views

# `/courses` entry point
router = routers.SimpleRouter()
router.register(
    r"courses",
    views.CourseViewSet,
    basename="courses",
)
course_router = routers.NestedSimpleRouter(
    router,
    r"courses",
    lookup="course",
)

# `/courses/<pk>/roles` entry point
course_router.register(
    r"roles",
    views.CourseRoleViewSet,
    basename="course-roles",
)

# `/courses/<pk>/tags` entry point
course_router.register(
    r"tags",
    views.TagViewSet,
    basename="course-tags",
)

# `/courses/<pk>/exercises` entry point
course_router.register(
    r"exercises",
    views.ExerciseViewSet,
    basename="course-exercises",
)

exercise_router = routers.NestedSimpleRouter(
    course_router, r"exercises", lookup="exercise"
)
# `/courses/<pk>/exercises/<pk>/choices` entry point
exercise_router.register(r"choices", views.ExerciseChoiceViewSet)
# `/courses/<pk>/exercises/<pk>/sub_exercises` entry point
exercise_router.register(r"sub_exercises", views.ExerciseViewSet)
# `/courses/<pk>/exercises/<pk>/testcases` entry point
exercise_router.register(r"testcases", views.ExerciseTestCaseViewSet)

# exercise solutions
# `/courses/<pk>/exercises/<pk>/solutions` entry point
exercise_router.register(r"solutions", views.ExerciseSolutionViewSet)

# `/courses/<pk>/templates` entry point
course_router.register(
    r"templates",
    views.EventTemplateViewSet,
    basename="course-templates",
)

# `/courses/<pk>/participations` entry point
course_router.register(
    r"participations",
    views.EventParticipationViewSet,
    basename="event-participations",
)


template_router = routers.NestedSimpleRouter(
    course_router, r"templates", lookup="template"
)
# `/courses/<pk>/templates/<pk>/rules` entry point
template_router.register(r"rules", views.EventTemplateRuleViewSet)

template_rule_router = routers.NestedSimpleRouter(
    template_router, r"rules", lookup="rule"
)

# `/courses/<pk>/templates/<pk>/rules/<pk>/clauses` entry point
template_rule_router.register(r"clauses", views.EventTemplateRuleClauseViewSet)

# `/courses/<pk>/events` entry point
course_router.register(
    r"events",
    views.EventViewSet,
    basename="course-events",
)

event_router = routers.NestedSimpleRouter(course_router, r"events", lookup="event")

# `/courses/<pk>/events/<pk>/participations` entry point
event_router.register(
    r"participations",
    views.EventParticipationViewSet,
    basename="event-participations",
)

participation_router = routers.NestedSimpleRouter(
    event_router, r"participations", lookup="participation"
)

# `/courses/<pk>/events/<pk>/participations/<pk>/slots` entry point
participation_router.register(
    r"slots", views.EventParticipationSlotViewSet, basename="participation-slots"
)


urlpatterns = [
    path("", include(router.urls)),
    path("", include(course_router.urls)),
    path("", include(event_router.urls)),
    path("", include(participation_router.urls)),
    path("", include(exercise_router.urls)),
    path("", include(template_router.urls)),
    path("", include(template_rule_router.urls)),
]
