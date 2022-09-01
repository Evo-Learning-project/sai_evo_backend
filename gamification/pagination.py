from core.pagination import CatchEmptyResultsPageNumberPagination


class LeaderboardPagination(CatchEmptyResultsPageNumberPagination):
    page_size = 10
