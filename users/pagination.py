from core.pagination import CatchEmptyResultsPageNumberPagination


class UserPagination(CatchEmptyResultsPageNumberPagination):
    page_size = 100
