from decimal import Decimal


def get_assessor_class(event):
    from courses.models import Event

    if event.event_type == Event.SELF_SERVICE_PRACTICE:
        return FullyAutomaticAssessor

    return BestEffortAutomaticAssessor


class SubmissionAssessor:
    def __init__(self, participation_slot):
        self.participation_slot = participation_slot
        self.slot_weight = (
            self.participation_slot.populating_rule.weight
            if self.participation_slot.populating_rule is not None
            else 1  # for backwards compatibility
        )

    def get_multiple_choice_submission_correctness(self, slot):
        selected_choices = slot.selected_choices.all()
        return sum([c.correctness for c in selected_choices])

    def get_programming_submission_correctness(self, slot):
        if slot.execution_results is None:
            return (
                0
                if slot.answer_text is None or len(slot.answer_text.strip()) == 0
                else None
            )
        try:
            passed_testcases = len(
                [t for t in slot.execution_results["tests"] if t["passed"]]
            )
            return passed_testcases
        except KeyError:
            # no test cases in execution results (e.g. compilation error in code)
            return 0

    def get_composite_exercise_submission_correctness(self, slot):
        # for composite exercises (i.e. COMPLETION, AGGREGATED) the correctness
        # is the sum of the correctness values of the sub-exercises
        assessable_sub_slots = slot.get_assessable_sub_slots()
        sub_slots_correctness = [
            (s, self.get_submission_correctness(s)) for s in assessable_sub_slots
        ]
        if any([c is None for _, c in sub_slots_correctness]):
            return None

        weighted_sub_slots_correctness = [
            Decimal(c) * Decimal(s.exercise.child_weight)
            for s, c in sub_slots_correctness
        ]

        correctness = sum(weighted_sub_slots_correctness)
        return correctness

    def get_manual_submission_correctness(self, slot):
        # TODO use ABC on this class and make this method abstract
        return None

    def get_submission_correctness(self, slot):
        from courses.models import Exercise

        exercise_type = slot.exercise.exercise_type

        if exercise_type in [Exercise.OPEN_ANSWER, Exercise.ATTACHMENT]:
            return self.get_manual_submission_correctness(slot)

        if exercise_type in [
            Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
        ]:
            return self.get_multiple_choice_submission_correctness(slot)

        if exercise_type in [Exercise.JS, Exercise.C]:
            return self.get_programming_submission_correctness(slot)

        return self.get_composite_exercise_submission_correctness(slot)

    def assess(self):
        """
        Takes in an EventParticipationSlot object (representing an exercise assigned to a user
        and the answer given to that exercise).

        Returns the score that results in applying the given rule with the given answer(s), or
        None if the exercise referenced by the given slot needs to be assessed manually.
        """
        if hasattr(self.participation_slot, "prefetched_max_choice_correctness"):
            # pass along prefetched value to the exercise to speed up computation of max_score
            self.participation_slot.exercise.prefetched_max_choice_correctness = (
                self.participation_slot.prefetched_max_choice_correctness
            )

        exercise_max_score = self.participation_slot.exercise.get_max_score()
        submission_correctness = self.get_submission_correctness(
            self.participation_slot
        )

        if submission_correctness is None:
            return None

        if exercise_max_score is None or exercise_max_score == 0:
            return 0

        # all or nothing exercise with partially incorrect answer
        if self.participation_slot.exercise.all_or_nothing and Decimal(
            submission_correctness
        ) < Decimal(exercise_max_score):
            return 0

        return (
            Decimal(submission_correctness)
            / Decimal(exercise_max_score)
            * Decimal(self.slot_weight or 0)
        )


class FullyAutomaticAssessor(SubmissionAssessor):
    """
    Used to assess submissions for events where no manual assessment
    is involved (for example, for events of type SELF_SERVICE_PRACTICE)
    """

    def get_manual_submission_correctness(self, slot):
        """
        Submissions for exercises that cannot be assessed automatically (e.g. open questions)
        are assigned 0 points, as this assessor isn't meant to be used in exams but
        rather in events where the score isn't important and the solution to the
        exercises is readily provided afterwards
        """
        return 0


class BestEffortAutomaticAssessor(SubmissionAssessor):
    """
    Used to assess submissions for events where manual assessment
    is involved; refuses to assess exercises like OPEN_ANSWER or ATTACHMENT,
    requiring manual action to complete the assessment
    """

    pass
