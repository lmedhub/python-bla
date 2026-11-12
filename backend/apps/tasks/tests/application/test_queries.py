import pytest

from apps.core.domain.errors import InvalidInputError
from apps.tasks.application.queries import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    Page,
    PageRequest,
)


class TestPageRequest:
    def test_defaults_to_the_first_page(self):
        page = PageRequest()

        assert (page.page, page.page_size) == (1, DEFAULT_PAGE_SIZE)

    @pytest.mark.parametrize("page_size", [1, MAX_PAGE_SIZE])
    def test_accepts_sizes_within_bounds(self, page_size: int):
        assert PageRequest(page_size=page_size).page_size == page_size

    @pytest.mark.parametrize("page_size", [0, MAX_PAGE_SIZE + 1, -5])
    def test_rejects_sizes_out_of_bounds(self, page_size: int):
        with pytest.raises(InvalidInputError) as error:
            PageRequest(page_size=page_size)

        assert list(error.value.fields) == ["page_size"]

    @pytest.mark.parametrize("page", [0, -1])
    def test_rejects_pages_below_one(self, page: int):
        with pytest.raises(InvalidInputError) as error:
            PageRequest(page=page)

        assert list(error.value.fields) == ["page"]

    def test_reports_both_fields_at_once(self):
        with pytest.raises(InvalidInputError) as error:
            PageRequest(page=0, page_size=0)

        assert set(error.value.fields) == {"page", "page_size"}

    def test_offset_skips_the_previous_pages(self):
        assert PageRequest(page=3, page_size=10).offset == 20


class TestPage:
    def test_a_page_past_the_end_is_empty_but_keeps_the_total(self):
        page: Page[str] = Page(items=[], total=25, request=PageRequest(page=9, page_size=10))

        assert page.items == []
        assert page.total == 25
        assert page.has_next is False

    def test_has_next_when_more_items_follow(self):
        page = Page(items=["a"] * 10, total=25, request=PageRequest(page=2, page_size=10))

        assert page.has_next is True
        assert page.has_previous is True

    def test_first_page_has_no_previous(self):
        page = Page(items=["a"] * 10, total=25, request=PageRequest(page=1, page_size=10))

        assert page.has_previous is False
