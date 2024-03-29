from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from course_tree.views import NodeCommentViewSet, PollNodeChoiceViewSet, TreeNodeViewSet
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

router.register(
    r"features",
    views.PretotypeDataCreationViewSet,
    basename="features",
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

# `/courses/<pk>/solutions` entry point
course_router.register(
    r"solutions",
    views.ExerciseSolutionViewSet,
    basename="course-exercise-solutions",
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


# exercise test cases
# `/courses/<pk>/exercises/<pk>/testcases` entry point
exercise_router.register(r"testcases", views.ExerciseTestCaseViewSet)

exercise_testcase_router = routers.NestedSimpleRouter(
    exercise_router, r"testcases", lookup="testcase"
)
# `/courses/<pk>/exercises/<pk>/testcases/<pk>/attachments` entry point
exercise_testcase_router.register(
    r"attachments", views.ExerciseTestCaseAttachmentViewSet
)
# exercise solutions
# `/courses/<pk>/exercises/<pk>/solutions` entry point
exercise_router.register(r"solutions", views.ExerciseSolutionViewSet)

exercise_solution_router = routers.NestedSimpleRouter(
    exercise_router,
    r"solutions",
    lookup="solution",
)

# `/courses/<pk>/exercises/<pk>/solutions/<pk>/comments` entry point
exercise_solution_router.register(r"comments", views.ExerciseSolutionCommentViewSet)

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

"""
    course_tree module urls
"""

# `/courses/<pk>/nodes` entry point
course_router.register(r"nodes", TreeNodeViewSet, basename="course-nodes")

tree_router = routers.NestedSimpleRouter(course_router, r"nodes", lookup="node")

# `/courses/<pk>/nodes/<pk>/children` entry point
tree_router.register(r"children", TreeNodeViewSet, basename="node-children")

# `/courses/<pk>/nodes/<pk>/comments` entry point
tree_router.register(r"comments", NodeCommentViewSet, basename="node-comments")
# `/courses/<pk>/nodes/<pk>/choices` entry point (only for poll nodes)
tree_router.register(r"choices", PollNodeChoiceViewSet, basename="node-choices")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(course_router.urls)),
    path("", include(event_router.urls)),
    path("", include(participation_router.urls)),
    path("", include(exercise_router.urls)),
    path("", include(exercise_testcase_router.urls)),
    path("", include(exercise_solution_router.urls)),
    path("", include(template_router.urls)),
    path("", include(template_rule_router.urls)),
    path("", include(tree_router.urls)),
]
