from django.db import models


class PostModelManager(models.Manager):
    def create(self, *args, **kwargs):
        from content.models import Content

        # pass kwarg content as text content to a new instance of Content model
        content = Content.objects.create(text_content=kwargs.pop("content", ""))
        # associate newly created Content to the ExerciseSolution that's being created
        kwargs["_content"] = content

        return super().create(*args, **kwargs)
