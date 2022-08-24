from django.contrib import admin

from gamification.models import *


@admin.register(GamificationContext)
class GamificationContextAdmin(admin.ModelAdmin):
    pass


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    pass


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    pass


@admin.register(BadgeDefinition)
class BadgeDefinitionAdmin(admin.ModelAdmin):
    pass


@admin.register(ActionDefinition)
class ActionDefinitionAdmin(admin.ModelAdmin):
    pass


class GoalLevelInline(admin.TabularInline):
    model = GoalLevel


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    inlines = [GoalLevelInline]


class GoalLevelActionDefinitionRequirementInline(admin.TabularInline):
    model = GoalLevelActionDefinitionRequirement


@admin.register(GoalLevel)
class GoalLevelAdmin(admin.ModelAdmin):
    inlines = [GoalLevelActionDefinitionRequirementInline]
