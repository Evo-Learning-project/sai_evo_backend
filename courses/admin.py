import nested_admin
from django.contrib import admin

from courses.models import *


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    pass


@admin.register(UserCoursePrivilege)
class UserCoursePrivilegeAdmin(admin.ModelAdmin):
    pass


class ExerciseChoiceInline(admin.TabularInline):
    model = ExerciseChoice


class ExerciseTestCaseInline(admin.TabularInline):
    model = ExerciseTestCase


class SubExerciseInline(admin.TabularInline):
    model = Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    inlines = [
        ExerciseChoiceInline,
        ExerciseTestCaseInline,
        SubExerciseInline,
    ]


class EventTemplateRuleClauseInline(nested_admin.NestedTabularInline):
    model = EventTemplateRuleClause


class EventTemplateRuleInline(nested_admin.NestedStackedInline):
    model = EventTemplateRule
    inlines = [EventTemplateRuleClauseInline]


class EventTemplateAdmin(nested_admin.NestedModelAdmin):
    inlines = [EventTemplateRuleInline]


admin.site.register(EventTemplate, EventTemplateAdmin)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass


class EventInstanceInline(admin.TabularInline):
    model = EventInstance


class ParticipationAssessmentSlotInline(admin.TabularInline):
    model = ParticipationAssessmentSlot
    readonly_fields = ("assessment_state", "exercise")


@admin.register(ParticipationAssessment)
class ParticipationAssessmentAdmin(admin.ModelAdmin):
    inlines = [ParticipationAssessmentSlotInline]
    readonly_fields = ("assessment_state",)


class ParticipationSubmissionSlotInline(admin.TabularInline):
    model = ParticipationSubmissionSlot


@admin.register(ParticipationSubmission)
class ParticipationSubmissionAdmin(admin.ModelAdmin):
    inlines = [ParticipationSubmissionSlotInline]


class EventInstanceSlotInline(admin.TabularInline):
    model = EventInstanceSlot


@admin.register(EventInstance)
class EventInstanceAdmin(admin.ModelAdmin):
    inlines = [EventInstanceSlotInline]


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    pass
