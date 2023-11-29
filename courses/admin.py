import nested_admin

from django.contrib import admin

from courses.models import *


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    readonly_fields = ("features",)


@admin.register(UserCourseEnrollment)
class UserCourseEnrollmentAdmin(admin.ModelAdmin):
    pass


@admin.register(UserCoursePrivilege)
class UserCoursePrivilegeAdmin(admin.ModelAdmin):
    pass


class ExerciseChoiceInline(admin.TabularInline):
    model = ExerciseChoice


class ExerciseTestCaseInline(admin.TabularInline):
    model = ExerciseTestCase


class ExerciseTestCaseAttachmentInline(admin.TabularInline):
    model = ExerciseTestCaseAttachment


class SubExerciseInline(admin.TabularInline):
    model = Exercise


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    inlines = [
        ExerciseChoiceInline,
        ExerciseTestCaseInline,
        SubExerciseInline,
    ]
    readonly_fields = ("parent", "public_tags", "private_tags")


class ContentInline(admin.TabularInline):
    model = Content


class ExerciseSolutionCommentInline(admin.TabularInline):
    model = ExerciseSolutionComment


@admin.register(ExerciseSolution)
class ExerciseSolutionAdmin(admin.ModelAdmin):
    inlines = [ExerciseSolutionCommentInline]
    pass


@admin.register(ExerciseChoice)
class ExerciseChoiceAdmin(admin.ModelAdmin):
    pass


@admin.register(ExerciseTestCase)
class ExerciseTestCaseAdmin(admin.ModelAdmin):
    inlines = [ExerciseTestCaseAttachmentInline]


@admin.register(ExerciseTestCaseAttachment)
class ExerciseTestCaseAttachmentAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


class EventTemplateRuleClauseInline(nested_admin.NestedTabularInline):
    model = EventTemplateRuleClause


class EventTemplateRuleInline(nested_admin.NestedStackedInline):
    model = EventTemplateRule
    inlines = [EventTemplateRuleClauseInline]


class EventTemplateAdmin(nested_admin.NestedModelAdmin):
    inlines = [EventTemplateRuleInline]


admin.site.register(EventTemplate, EventTemplateAdmin)


@admin.register(EventTemplateRule)
class EventTemplateRuleAdmin(admin.ModelAdmin):
    pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    readonly_fields = ("state", "template")


@admin.register(EventParticipationSlot)
class EventParticipationSlotAdmin(admin.ModelAdmin):
    readonly_fields = (
        "exercise",
        "selected_choices",
        "participation",
        "parent",
    )


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    readonly_fields = ("begin_timestamp", "event", "user")


@admin.register(PretotypeData)
class PretotypeDataAdmin(admin.ModelAdmin):
    pass
