from courses.logic.privileges import check_privilege, MANAGE_COURSE_TREE_NODES
from courses.policies import BaseAccessPolicy


class TreeNodePolicy(BaseAccessPolicy):
    statements = [
        {
            "action": ["retrieve", "list", "download", "root_id", "thumbnail"],
            "principal": ["*"],
            "effect": "allow",
            # "condition": "is_visible_to",
        },
        {
            "action": ["create"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_create_permission_over_resource_type",
        },
        {
            "action": ["update", "partial_update", "move"],
            "principal": ["authenticated"],
            "effect": "allow",
            "condition": "has_update_permission_over_resource_type",
        },
        # {
        #     "action": ["update", "partial_update"],
        #     "principal": ["authenticated"],
        #     "effect": "allow",
        #     "condition": "has_teacher_privileges:update_course",
        # },
    ]

    def has_create_permission_over_resource_type(self, request, view, action):
        resource_type = request.data.get("resourcetype")

        if resource_type is None:
            # let serializer handle invalid input
            return True

        if resource_type == "RootCourseTreeNode":
            # users cannot create root nodes directly
            return False

        # TODO use different permissions depending on the resource type (distinguish between resources that can only be created by teachers)
        return check_privilege(
            request.user, view.kwargs.get("course_pk"), MANAGE_COURSE_TREE_NODES
        )

    def has_update_permission_over_resource_type(self, request, view, action):
        resource_type = request.data.get("resourcetype")

        if resource_type is None:
            # let serializer handle invalid input
            return True

        if resource_type == "RootCourseTreeNode":
            # users cannot create root nodes directly
            return False

        # TODO use different permissions depending on the resource type (distinguish between resources that can only be created by teachers)
        # TODO for student-created nodes, like PostNode for example (when it'll be implemented), check author
        return check_privilege(
            request.user, view.kwargs.get("course_pk"), MANAGE_COURSE_TREE_NODES
        )
