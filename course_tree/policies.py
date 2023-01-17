from courses.logic.privileges import check_privilege, MANAGE_COURSE_TREE_NODES
from courses.policies import BaseAccessPolicy
from .models import RootCourseTreeNode


class BaseTreeAccessPolicy(BaseAccessPolicy):
    pass


class TreeNodePolicy(BaseTreeAccessPolicy):
    statements = [
        {
            "action": ["retrieve", "list", "download", "root_id", "thumbnail"],
            "principal": ["authenticated"],
            "effect": "allow",
            # "condition": "is_visible_to",
        },
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:manage_course_tree_nodes",
        },
        {
            "action": [
                "update",
                "partial_update",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_course_tree_nodes and not is_root_node",
        },
        {
            "action": ["destroy", "move"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_course_tree_nodes and not is_root_node",
        },
    ]

    def is_root_node(self, request, view, action):
        node = view.get_object()
        return isinstance(node, RootCourseTreeNode)


class NodeCommentPolicy(BaseTreeAccessPolicy):
    statements = [
        {
            "action": [
                "retrieve",
                "list",
                "create",
            ],
            "principal": ["authenticated"],
            "effect": "allow",
            # "condition": "is_visible_to",
        },
        {
            "action": ["destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "is_own_comment or has_teacher_privileges:manage_course_tree_nodes",
        },
    ]

    def is_own_comment(self, request, view, action):
        return view.get_object().user == request.user


# TODO review
class PollNodeChoicePolicy(BaseTreeAccessPolicy):
    statements = [
        {
            "action": ["retrieve", "list"],
            "principal": ["authenticated"],
            "effect": "allow",
        },
        {
            "action": ["vote"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition_expression": "has_teacher_privileges:manage_course_tree_nodes or can_vote",
        },
        {
            "action": ["create", "partial_update", "update", "destroy"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_teacher_privileges:manage_course_tree_nodes",
        },
    ]

    def can_vote(self, request, view, action):
        poll = view.get_object().poll
        return poll.can_vote(request.user)
