from polymorphic_tree.managers import PolymorphicMPTTModelManager


class CourseTreeNodeManager(PolymorphicMPTTModelManager):
    def get_queryset(self):
        from .querysets import CourseTreeNodeQuerySet

        return CourseTreeNodeQuerySet(self.model, using=self._db)
