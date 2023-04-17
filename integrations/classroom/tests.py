from django.test import TestCase

from integrations.classroom.integration import GoogleClassroomIntegration


class ClassroomIntegrationTestCase(TestCase):
    def setUp(self):
        self.integration = GoogleClassroomIntegration()
