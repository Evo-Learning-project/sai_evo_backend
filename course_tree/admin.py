from django.contrib import admin
from polymorphic_tree.admin import (
    PolymorphicMPTTParentModelAdmin,
    PolymorphicMPTTChildModelAdmin,
)

from course_tree.models import (
    AnnouncementNode,
    BaseCourseTreeNode,
    LessonNode,
    FileNode,
    NodeComment,
    PollNode,
    PollNodeChoice,
    PollNodeParticipation,
    TopicNode,
    RootCourseTreeNode,
)


class BaseChildAdmin(PolymorphicMPTTChildModelAdmin):
    GENERAL_FIELDSET = (
        None,
        {
            "fields": ("parent",),
        },
    )

    base_model = BaseCourseTreeNode
    base_fieldsets = (GENERAL_FIELDSET,)


# Optionally some custom admin code


class RootNodeAdmin(BaseChildAdmin):
    pass


class TopicNodeAdmin(BaseChildAdmin):
    pass


class AnnouncementNodeAdmin(BaseChildAdmin):
    pass


class PollNodeAdmin(BaseChildAdmin):
    pass


class LessonNodeAdmin(BaseChildAdmin):
    pass


class FileNodeAdmin(BaseChildAdmin):
    list_display = ("file",)


# Create the parent admin that combines it all:


class TreeNodeParentAdmin(PolymorphicMPTTParentModelAdmin):
    base_model = BaseCourseTreeNode
    child_models = (
        RootCourseTreeNode,
        TopicNode,
        LessonNode,
        FileNode,
    )

    list_display = (
        "displayed_name",
        "actions_column",
    )

    class Media:
        css = {"all": ("admin/treenode/admin.css",)}


@admin.register(NodeComment)
class NodeCommentAdmin(admin.ModelAdmin):
    readonly_fields = ("created", "modified")


@admin.register(PollNodeChoice)
class PollNodeChoiceAdmin(admin.ModelAdmin):
    pass


@admin.register(PollNodeParticipation)
class PollNodeParticipation(admin.ModelAdmin):
    pass


admin.site.register(RootCourseTreeNode, RootNodeAdmin)
admin.site.register(TopicNode, TopicNodeAdmin)
admin.site.register(LessonNode, LessonNodeAdmin)
admin.site.register(FileNode, FileNodeAdmin)
admin.site.register(BaseCourseTreeNode, TreeNodeParentAdmin)
admin.site.register(AnnouncementNode, AnnouncementNodeAdmin)
admin.site.register(PollNode, PollNodeAdmin)
