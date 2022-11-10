from django.contrib import admin
from polymorphic_tree.admin import (
    PolymorphicMPTTParentModelAdmin,
    PolymorphicMPTTChildModelAdmin,
)

from course_tree.models import (
    BaseCourseTreeNode,
    LessonNode,
    FileNode,
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


admin.site.register(RootCourseTreeNode, RootNodeAdmin)
admin.site.register(TopicNode, TopicNodeAdmin)
admin.site.register(LessonNode, LessonNodeAdmin)
admin.site.register(FileNode, FileNodeAdmin)
admin.site.register(BaseCourseTreeNode, TreeNodeParentAdmin)
