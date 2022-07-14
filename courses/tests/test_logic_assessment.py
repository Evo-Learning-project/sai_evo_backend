from courses.models import (
    Course,
    Event,
    EventParticipation,
    EventTemplateRule,
    Exercise,
)
from django.test import TestCase
from users.models import User

from data import users, courses, exercises, events

from django.utils import timezone


class SubmissionAssessorTestCase(TestCase):
    def setUp(self):
        self.teacher_1 = User.objects.create(**users.teacher_1)
        self.course = Course.objects.create(creator=self.teacher_1, **courses.course_1)

        self.student_1 = User.objects.create(**users.student_1)
        self.student_2 = User.objects.create(**users.student_2)

        self.mmc = Exercise.objects.create(course=self.course, **exercises.mmc_priv_1)
        self.msc = Exercise.objects.create(course=self.course, **exercises.msc_priv_1)
        self.clz = Exercise.objects.create(course=self.course, **exercises.cloze_prv_1)
        self.open = Exercise.objects.create(course=self.course, **exercises.open_priv_1)
        self.js = Exercise.objects.create(course=self.course, **exercises.js_prv_1)

        self.event: Event = Event.objects.create(
            course=self.course, creator=self.teacher_1, **events.exam_1_one_at_a_time
        )

        self.rule_mmc = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            max_score=2,
        )
        self.rule_msc = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            max_score=2,
        )
        self.rule_clz = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            max_score=2,
        )
        self.rule_open = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            max_score=2,
        )
        self.rule_js = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            max_score=2,
        )
        self.rule_mmc.exercises.set([self.mmc])
        self.rule_msc.exercises.set([self.msc])
        self.rule_clz.exercises.set([self.clz])
        self.rule_open.exercises.set([self.open])
        self.rule_js.exercises.set([self.js])

        # open event
        self.event.state = Event.PLANNED
        self.event.begin_timestamp = timezone.localdate(timezone.now())

        self.participation = EventParticipation.objects.create(
            event_id=self.event.pk, user=self.student_1
        )
        self.slot_mmc = self.participation.slots.get(populating_rule=self.rule_mmc)
        self.slot_msc = self.participation.slots.get(populating_rule=self.rule_msc)
        self.slot_clz = self.participation.slots.get(populating_rule=self.rule_clz)
        self.slot_open = self.participation.slots.get(populating_rule=self.rule_open)
        self.slot_js = self.participation.slots.get(populating_rule=self.rule_js)

    def test_event_max_score(self):
        """
        Shows that the max_score property of an event is computed by summing
        the max_score property of its rules, each multiplied by the rule's
        amount value
        """
        self.assertEqual(self.event.max_score, 10)

        self.rule_js.amount = 2
        self.rule_js.save()
        self.assertEqual(self.event.max_score, 12)

        """
        Shows that, when wrote to, the max_score property of an event
        causes all rules to be assigned the same weight to evenly
        distribute the new value
        """

        self.event.max_score = 21

        self.rule_msc.refresh_from_db()
        self.rule_mmc.refresh_from_db()
        self.rule_clz.refresh_from_db()
        self.rule_open.refresh_from_db()
        self.rule_js.refresh_from_db()

        self.assertEqual(self.rule_msc.max_score, 3.5)
        self.assertEqual(self.rule_mmc.max_score, 3.5)
        self.assertEqual(self.rule_clz.max_score, 3.5)
        self.assertEqual(self.rule_open.max_score, 3.5)
        self.assertEqual(self.rule_js.max_score, 3.5)

        # reset rules
        self.rule_msc.max_score = 2
        self.rule_msc.save()
        self.rule_mmc.max_score = 2
        self.rule_mmc.save()
        self.rule_clz.max_score = 2
        self.rule_clz.save()
        self.rule_open.max_score = 2
        self.rule_open.save()
        self.rule_js.max_score = 2
        self.rule_js.amount = 1
        self.rule_js.save()

        self.rule_msc.refresh_from_db()
        self.rule_mmc.refresh_from_db()
        self.rule_clz.refresh_from_db()
        self.rule_open.refresh_from_db()
        self.rule_js.refresh_from_db()

    def test_multiple_choice_single_selection_assessment(self):
        choices = self.msc.choices.all()
        correct_choice = choices.get(correctness_percentage=100)
        partially_correct_choice = choices.get(correctness_percentage=50)
        incorrect_choice = choices.get(correctness_percentage=0)

        # selected choices are initially empty
        self.assertFalse(self.slot_msc.selected_choices.exists())

        max_score = self.slot_msc.populating_rule.max_score

        """
        Show that selecting a choice with 100% correctness gives the
        full score of the populating rule
        """
        self.slot_msc.selected_choices.set([correct_choice])
        self.assertEqual(self.slot_msc.score, max_score)

        """
        Show that selecting a choice with 50% correctness gives
        half the score of the populating rule
        """
        self.slot_msc.selected_choices.set([partially_correct_choice])
        self.assertEqual(self.slot_msc.score, max_score / 2)

        """
        Show that selecting a choice with 0% correctness gives score 0
        """
        self.slot_msc.selected_choices.set([incorrect_choice])
        self.assertEqual(self.slot_msc.score, 0)

        """
        Show that selecting a choice with negative correctness
        gives negative score
        """
        incorrect_choice.correctness_percentage = -25
        incorrect_choice.save()
        self.slot_msc.selected_choices.set([incorrect_choice])
        self.assertEqual(self.slot_msc.score, -0.5)

        """
        Changing the populating rule max_score property keeps
        the slot's score in sync
        """
        new_max_score = 10
        self.slot_msc.selected_choices.set([correct_choice])
        self.rule_msc.max_score = new_max_score
        self.rule_msc.save()

        self.slot_msc.refresh_from_db()  # apparently need to refetch

        self.assertEqual(self.slot_msc.score, new_max_score)

    def test_cloze_assessment(self):
        sub_exercises = self.clz.sub_exercises.all()
        sub_weight_50 = sub_exercises.get(_ordering=0)
        sub_weight_25_1 = sub_exercises.get(_ordering=1)
        sub_weight_25_2 = sub_exercises.get(_ordering=2)

        sub_1_correct_choice = sub_weight_50.choices.get(correctness_percentage=100)
        sub_2_correct_choice = sub_weight_25_1.choices.get(correctness_percentage=100)
        sub_3_correct_choice = sub_weight_25_2.choices.get(correctness_percentage=100)
        sub_2_partially_correct_choice = sub_weight_25_1.choices.get(
            correctness_percentage=50
        )
        sub_2_incorrect_choice = sub_weight_25_1.choices.get(correctness_percentage=-10)
        sub_3_incorrect_choice = sub_weight_25_2.choices.get(correctness_percentage=0)

        sub_slot_1 = self.slot_clz.sub_slots.get(exercise=sub_weight_50)
        sub_slot_2 = self.slot_clz.sub_slots.get(exercise=sub_weight_25_1)
        sub_slot_3 = self.slot_clz.sub_slots.get(exercise=sub_weight_25_2)

        """
        Show that, for cloze exercises, the overall correctness is the
        weighted sum of the correctness of the sub-exercises
        """
        sub_slot_1.selected_choices.set([sub_1_correct_choice])
        sub_slot_2.selected_choices.set([sub_2_partially_correct_choice])
        sub_slot_3.selected_choices.set([sub_3_incorrect_choice])

        slot_clz_max_score = self.slot_clz.populating_rule.max_score

        # 100% * 50% (first sub-exercise)  + 50% * 25% (second) + 0% * 25% (third)
        self.assertEqual(self.slot_clz.score / slot_clz_max_score, 0.625)

        # all correct answers
        sub_slot_1.selected_choices.set([sub_1_correct_choice])
        sub_slot_2.selected_choices.set([sub_2_correct_choice])
        sub_slot_3.selected_choices.set([sub_3_correct_choice])

        slot_clz_max_score = self.slot_clz.populating_rule.max_score

        # 100% * 50% (first sub-exercise)  + 100% * 25% (second) + 100% * 25% (third)
        self.assertEqual(self.slot_clz.score / slot_clz_max_score, 1)

        # one answer has negative score
        sub_slot_1.selected_choices.set([sub_1_correct_choice])
        sub_slot_2.selected_choices.set([sub_2_incorrect_choice])
        sub_slot_3.selected_choices.set([sub_3_correct_choice])

        # 100% * 50% (first sub-exercise)  - 10% * 25% (second) + 100% * 25% (third)
        self.assertEqual(self.slot_clz.score / slot_clz_max_score, 0.725)

    def test_open_answer_assessment(self):
        pass

    def test_js_assessment(self):
        pass
