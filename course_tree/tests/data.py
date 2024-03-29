from course_tree.models import LessonNode, PollNode, AnnouncementNode

lesson_node_1 = {
    "resourcetype": "LessonNode",
    "title": "Lesson 01",
    "body": "Body of lesson 01",
    "state": LessonNode.LessonState.DRAFT,
}

lesson_node_2 = {
    "resourcetype": "LessonNode",
    "title": "Lesson 02",
    "body": "Body of lesson 02",
    "state": LessonNode.LessonState.DRAFT,
}

lesson_node_3 = {
    "resourcetype": "LessonNode",
    "title": "Lesson 03",
    "body": "Body of lesson 03",
    "state": LessonNode.LessonState.DRAFT,
}

poll_node_1 = {
    "resourcetype": "PollNode",
    "text": "Poll text",
    "state": PollNode.PollState.DRAFT,
}

announcement_node_1 = {
    "resourcetype": "AnnouncementNode",
    "body": "Announcement text",
    "state": AnnouncementNode.AnnouncementState.DRAFT,
}

topic_node_1 = {
    "resourcetype": "TopicNode",
    "name": "Topic 1",
}
