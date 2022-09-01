from core.pagination import CatchEmptyResultsPageNumberPagination


class ExercisePagination(CatchEmptyResultsPageNumberPagination):
    page_size = 4


class EventParticipationPagination(CatchEmptyResultsPageNumberPagination):
    page_size = 8
