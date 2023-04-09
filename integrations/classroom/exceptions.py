class MissingGoogleOAuth2Credentials(Exception):
    pass


class InvalidGoogleOAuth2Credentials(Exception):
    pass


class UnrecoverableGoogleClassroomError(Exception):
    pass


class DomainSettingsError(UnrecoverableGoogleClassroomError):
    pass


class CannotEnrollTeacher(Exception):
    pass
