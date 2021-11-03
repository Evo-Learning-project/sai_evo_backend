def get_assessor_class(event):
    from courses.models import Event

    if event.event_type == Event.SELF_SERVICE_PRACTICE:
        return FullyAutomaticAssessor

    return BestEffortAutomaticAssessor


def get_default_assessment_rule():
    from courses.models import ExerciseAssessmentRule

    return ExerciseAssessmentRule()


class SubmissionAssessor:
    def __init__(self, assessment_slot):
        from courses.models import ExerciseAssessmentRule

        self.submission_slot = assessment_slot.submission
        self.assessment_slot = assessment_slot

        try:
            self.rule = assessment_slot.exercise.get_assessment_rule(
                assessment_slot.event
            )
            # self.rule = assessment_slot.event.assessment_rules.get(
            #     exercise=assessment_slot.exercise
            # )
        except ExerciseAssessmentRule.DoesNotExist:
            self.rule = get_default_assessment_rule()

    def assess_multiple_choice(self):
        if self.submission_slot.selected_choice is None:
            return self.rule.points_for_blank
        return (
            self.rule.points_for_correct
            if self.submission_slot.selected_choice.correct
            else self.rule.points_for_incorrect
        )

    def assess_js(self):
        # TODO implement
        pass

    def assess_composite_exercise(self):
        # for comosite exercises (i.e. MULTIPLE_CHOICE_MULTIPLE_POSSIBLE, COMPLETION,
        # AGGREGATED) the score is the sum of the sub-exercises
        sub_slots_score = sum([s.score for s in self.assessment_slot.sub_slots.all()])

        return (
            0
            if (
                self.rule.minimum_score_threshold is not None
                and sub_slots_score < self.rule.minimum_score_threshold
            )
            else sub_slots_score
        )

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


# class FullyManualAssessor(SubmissionAssessor):
#     """
#     Used to override all the assessment rules and always require manual
#     assessment for all kinds of exercises
#     """

#     def assess(self):
#         return None


class BestEffortAutomaticAssessor(SubmissionAssessor):
    """
    Used to assess submissions for events where manual assessment
    is involved; refuses to assess exercises like OPEN_ANSWER or ATTACHMENT,
    requiring manual action to complete the assessment
    """

    pass


# class ManualAggregatedExerciseAssessor(SubmissionAssessor):
#     """
#     Used to enable custom assessment for aggregated exercises by disabling
#     automatic assessment for such exercise types
#     """

#     def assess_composite_exercise(self):
#         from courses.models import Exercise

#         if self.submission_slot.exercise.exercise_type == Exercise.AGGREGATED:
#             return None

#         return super().assess_composite_exercise()
