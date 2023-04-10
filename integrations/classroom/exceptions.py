class UnrecoverableGoogleClassroomError(Exception):
    pass


class MissingGoogleOAuth2Credentials(UnrecoverableGoogleClassroomError):
    pass


class InvalidGoogleOAuth2Credentials(UnrecoverableGoogleClassroomError):
    pass


class DomainSettingsError(UnrecoverableGoogleClassroomError):
    pass


class CannotEnrollTeacher(UnrecoverableGoogleClassroomError):
    pass
