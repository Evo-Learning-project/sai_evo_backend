from core.pagination import CatchEmptyResultsPageNumberPagination


class CourseTreeNodePagination(CatchEmptyResultsPageNumberPagination):
    page_size = 2


class CourseTreeChildrenNodePagination(CatchEmptyResultsPageNumberPagination):
    page_size = 1
