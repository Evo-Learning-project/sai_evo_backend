def get_assessor_class(event):
    from courses.models import Event

    if event.event_type == Event.SELF_SERVICE_PRACTICE:
        return FullyAutomaticAssessor

    return BestEffortAutomaticAssessor


class SubmissionAssessor:
    def __init__(self, participation_slot):
        self.participation_slot = participation_slot

    def assess_multiple_choice(self):
        return sum(
            [
                c.score_selected
                if c in self.participation_slot.selected_choices.all()
                else c.score_unselected
                for c in self.participation_slot.exercise.choices.all()
            ]
        )

    def assess_programming_exercise(self):
        if self.participation_slot.execution_results is None:
            return (
                0
                if self.participation_slot.answer_text is None
                or len(self.participation_slot.answer_text.strip()) == 0
                else None
            )

        try:
            tests = self.participation_slot.execution_results["tests"]
            return len([t for t in tests if t["passed"]])
        except KeyError:
            return 0

    def assess_composite_exercise(self):
        # for comosite exercises (i.e. COMPLETION, AGGREGATED)
        # the score is the sum of the scores of the sub-exercises
        sub_slots_scores = [s.score for s in self.participation_slot.sub_slots.all()]

        if any([s is None for s in sub_slots_scores]):
            return None

        return sum(sub_slots_scores)

    def get_no_automatic_assessment_score(self):
        # TODO use ABC on this class and make this method abstract
        return None

    def assess(self):
        """
        Takes in an EventParticipationSlot object (representing an exercise assigned to a user
        and the answer given to that exercise).

        Returns the score that results in applying the given rule with the given answer(s), or
        None if the exercise referenced by the given slot needs to be assessed manually.
        """
        from courses.models import Exercise

        exercise_type = self.participation_slot.exercise.exercise_type

        if exercise_type in [Exercise.OPEN_ANSWER, Exercise.ATTACHMENT]:
            return self.get_no_automatic_assessment_score()

        if exercise_type in [
            Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE,
            Exercise.MULTIPLE_CHOICE_MULTIPLE_POSSIBLE,
        ]:
            return self.assess_multiple_choice()

        if exercise_type in [Exercise.JS, Exercise.C]:
            return self.assess_programming_exercise()

        return self.assess_composite_exercise()


class FullyAutomaticAssessor(SubmissionAssessor):
    """
    Used to assess submissions for events where no manual assessment
    is involved (for example, for events of type SELF_SERVICE_PRACTICE)
    """

    def get_no_automatic_assessment_score(self):
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
