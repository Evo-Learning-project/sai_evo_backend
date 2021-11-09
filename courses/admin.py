from django.contrib import admin

from courses.models import *


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
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


class EventTemplateRuleClauseInline(admin.StackedInline):
    model = EventTemplateRuleClause


class EventTemplateRuleInline(admin.TabularInline):
    model = EventTemplateRule
    inlines = [EventTemplateRuleClauseInline]


@admin.register(EventTemplate)
class EventTemplateAdmin(admin.ModelAdmin):
    inlines = [EventTemplateRuleInline]
