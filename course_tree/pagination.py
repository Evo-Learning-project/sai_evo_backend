from core.pagination import CatchEmptyResultsPageNumberPagination


class CourseTreeNodePagination(CatchEmptyResultsPageNumberPagination):
    page_size = 10


class CourseTreeChildrenNodePagination(CatchEmptyResultsPageNumberPagination):
    page_size = 10
