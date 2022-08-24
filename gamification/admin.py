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


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    pass


@admin.register(GoalLevel)
class GoalLevelAdmin(admin.ModelAdmin):
    pass
