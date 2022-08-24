def get_gamification_engine():
    from gamification.engine import ActionPayload, dispatch_action

    class GamificationEngine:
        @staticmethod
        def dispatch_action(payload: ActionPayload):
            return dispatch_action(payload)
        

    return GamificationEngine
