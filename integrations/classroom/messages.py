EXAM_PUBLISHED = "EXAM_PUBLISHED"
VIEW_LESSON_ON_EVO = "VIEW_LESSON_ON_EVO"


def get_message(message_id):
    # TODO use translation
    messages = {
        EXAM_PUBLISHED: "Accedi a questo esame su Evo Learning",
        VIEW_LESSON_ON_EVO: "Visualizza questa lezione su Evo Learning",
    }
    return messages[message_id]
