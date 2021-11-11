def get_assessor_class(event):
    from courses.models import Event

    if event.event_type == Event.SELF_SERVICE_PRACTICE:
        return FullyAutomaticAssessor

    return BestEffortAutomaticAssessor


class SubmissionAssessor:
    def __init__(self, assessment_slot):
        self.submission_slot = assessment_slot.submission
        self.assessment_slot = assessment_slot

    def assess_multiple_choice(self):
        if self.submission_slot.selected_choice is None:
            # TODO figure out if there's anything smarter you can do
            return 0

        return self.submission_slot.selected_choice.score

    def assess_js(self):
        # TODO implement
        pass

    def assess_composite_exercise(self):
        # for comosite exercises (i.e. MULTIPLE_CHOICE_MULTIPLE_POSSIBLE, COMPLETION,
        # AGGREGATED) the score is the sum of the scores of the sub-exercises
        sub_slots_score = sum([s.score for s in self.assessment_slot.sub_slots.all()])

        return sub_slots_score

    def get_no_automatic_assessment_score(self):
        return None

    def assess(self):
        """
        Takes in a ParticipationSubmissionSlot object (representing an exercise assigned to a user
        and the answer given to that exercise).

        Returns the score that results in applying the given rule with the given answer(s), or
        None if the exercise referenced by the given slot needs to be assessed manually.
        """
        from courses.models import Exercise

        if self.rule.require_manual_assessment:
            return None

        exercise_type = self.submission_slot.exercise.exercise_type

        if (
            exercise_type == Exercise.OPEN_ANSWER
            or exercise_type == Exercise.ATTACHMENT
        ):
            return self.get_no_automatic_assessment_score()

        if exercise_type == Exercise.MULTIPLE_CHOICE_SINGLE_POSSIBLE:
            return self.assess_multiple_choice()

        if self.submission_slot.exercise.exercise_type == Exercise.JS:
            return self.assess_js()

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