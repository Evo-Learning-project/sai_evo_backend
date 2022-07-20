from decimal import Decimal
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
            weight=2,
        )
        self.rule_msc = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            weight=2,
        )
        self.rule_clz = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            weight=2,
        )
        self.rule_open = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            weight=2,
        )
        self.rule_js = EventTemplateRule.objects.create(
            template=self.event.template,
            rule_type=EventTemplateRule.ID_BASED,
            weight=2,
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
        the weight property of its rules, each multiplied by the rule's
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

        self.assertEqual(self.rule_msc.weight, 3.5)
        self.assertEqual(self.rule_mmc.weight, 3.5)
        self.assertEqual(self.rule_clz.weight, 3.5)
        self.assertEqual(self.rule_open.weight, 3.5)
        self.assertEqual(self.rule_js.weight, 3.5)

        # reset rules
        self.rule_msc.weight = 2
        self.rule_msc.save()
        self.rule_mmc.weight = 2
        self.rule_mmc.save()
        self.rule_clz.weight = 2
        self.rule_clz.save()
        self.rule_open.weight = 2
        self.rule_open.save()
        self.rule_js.weight = 2
        self.rule_js.amount = 1
        self.rule_js.save()

        self.rule_msc.refresh_from_db()
        self.rule_mmc.refresh_from_db()
        self.rule_clz.refresh_from_db()
        self.rule_open.refresh_from_db()
        self.rule_js.refresh_from_db()

    def test_multiple_choice_single_selection_assessment(self):
        """
        Shows that the max possible score for a multiple choice, single selection exercise
        is the correctness value of the choice(s) with the highest correctness
        """
        self.assertEqual(self.msc.get_max_score(), 1)

        choices = self.msc.choices.all()
        correct_choice = choices.get(correctness=1)
        partially_correct_choice = choices.get(correctness=0.5)
        incorrect_choice = choices.get(correctness=0)

        # selected choices are initially empty
        self.assertFalse(self.slot_msc.selected_choices.exists())

        weight = self.slot_msc.populating_rule.weight

        """
        Show that selecting a choice with 100% correctness gives the
        full score of the populating rule
        """
        self.slot_msc.selected_choices.set([correct_choice])
        self.assertEqual(self.slot_msc.score, weight)

        """
        Show that selecting a choice with 50% correctness gives
        half the score of the populating rule
        """
        self.slot_msc.selected_choices.set([partially_correct_choice])
        self.assertEqual(self.slot_msc.score, weight / 2)

        """
        Show that selecting a choice with 0% correctness gives score 0
        """
        self.slot_msc.selected_choices.set([incorrect_choice])
        self.assertEqual(self.slot_msc.score, 0)

        """
        Show that selecting a choice with negative correctness
        gives negative score
        """
        incorrect_choice.correctness = -0.25
        incorrect_choice.save()
        self.slot_msc.selected_choices.set([incorrect_choice])
        self.assertEqual(self.slot_msc.score, -0.5)

        """
        Changing the populating rule weight property keeps
        the slot's score in sync
        """
        new_weight = 10
        self.slot_msc.selected_choices.set([correct_choice])
        self.rule_msc.weight = new_weight
        self.rule_msc.save()

        self.slot_msc.refresh_from_db()  # apparently need to refetch

        self.assertEqual(self.slot_msc.score, new_weight)

    def test_multiple_choice_multiple_selection_assessment(self):
        """
        Shows that, for checkbox exercises, the max score is equal to the sum
        of the correctness value of the correct (i.e. correctness > 0) choices
        """
        self.assertEqual(self.mmc.get_max_score(), 2.5)

        choices = self.mmc.choices.all()
        correct_choices = choices.filter(correctness__gt=0)
        incorrect_choice = choices.get(correctness=-1)

        # selected choices are initially empty
        self.assertFalse(self.slot_mmc.selected_choices.exists())

        weight = self.slot_mmc.populating_rule.weight

        """
        Show that selecting all and only the choices with positive
        correctness gives the full score of the populating rule
        """
        self.slot_mmc.selected_choices.set([c for c in correct_choices])
        self.assertEqual(self.slot_mmc.score, weight)

        """
        Show that selecting a choice with negative correctness decreases
        the corresponding score
        """
        self.slot_mmc.selected_choices.add(incorrect_choice)
        self.assertEqual(self.slot_mmc.score, Decimal("1.2"))

    def test_cloze_assessment(self):
        """
        Shows that the max_score for a completion exercise is the
        weighted sum of the max_scores of its sub_exercises
        """
        self.assertEqual(self.clz.get_max_score(), 4)

        sub_exercises = self.clz.sub_exercises.all()
        sub_weight_2 = sub_exercises.get(_ordering=0)
        sub_weight_1_1 = sub_exercises.get(_ordering=1)
        sub_weight_1_2 = sub_exercises.get(_ordering=2)

        sub_1_correct_choice = sub_weight_2.choices.get(correctness=1)
        sub_2_correct_choice = sub_weight_1_1.choices.get(correctness=1)
        sub_3_correct_choice = sub_weight_1_2.choices.get(correctness=1)
        sub_2_partially_correct_choice = sub_weight_1_1.choices.get(correctness=0.5)
        sub_2_incorrect_choice = sub_weight_1_1.choices.get(correctness=-0.1)
        sub_3_incorrect_choice = sub_weight_1_2.choices.get(correctness=0)

        sub_slot_1 = self.slot_clz.sub_slots.get(exercise=sub_weight_2)
        sub_slot_2 = self.slot_clz.sub_slots.get(exercise=sub_weight_1_1)
        sub_slot_3 = self.slot_clz.sub_slots.get(exercise=sub_weight_1_2)

        """
        Show that, for cloze exercises, the overall correctness is the
        weighted sum of the correctness of the sub-exercises
        """
        sub_slot_1.selected_choices.set([sub_1_correct_choice])
        sub_slot_2.selected_choices.set([sub_2_partially_correct_choice])
        sub_slot_3.selected_choices.set([sub_3_incorrect_choice])

        # 1 * 2 (first sub-exercise)  + 0.5 * 1 (second) + 0 * 1 (third) = 2.5
        # max score for the exercise is 4, max score for the slot is 2
        # ==> 2.5 / 4 * 2 = 1.25
        self.assertEqual(self.slot_clz.score, Decimal("1.25"))

        # all correct answers
        sub_slot_1.selected_choices.set([sub_1_correct_choice])
        sub_slot_2.selected_choices.set([sub_2_correct_choice])
        sub_slot_3.selected_choices.set([sub_3_correct_choice])

        # 1 * 2 (first sub-exercise)  + 1 * 1 (second) + 1 * 1 (third)
        # ==> 4 / 4 * 2 = 2
        self.assertEqual(self.slot_clz.score, Decimal("2"))

        # one answer has negative score
        sub_slot_1.selected_choices.set([sub_1_correct_choice])
        sub_slot_2.selected_choices.set([sub_2_incorrect_choice])
        sub_slot_3.selected_choices.set([sub_3_correct_choice])

        # 1 * 2 (first sub-exercise)  - 0.1 * 1 (second) + 1 * 1 (third)
        # ==> 2.9 / 4 * 2 = 1.45
        self.assertEqual(self.slot_clz.score, Decimal("1.45"))

    def test_open_answer_assessment(self):
        pass

    def test_js_assessment(self):
        # TODO implement
        pass
