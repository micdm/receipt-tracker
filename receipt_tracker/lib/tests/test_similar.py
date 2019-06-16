import pytest
from pytest import fixture

from receipt_tracker.lib.similar import SimilarProductFinder
from receipt_tracker.models import Product

pytestmark = pytest.mark.django_db


@fixture
def product_foo(mixer):
    return mixer.blend(Product, user_friendly_name='foo foo')


@fixture
def product_bar(mixer):
    return mixer.blend(Product, user_friendly_name='bar bar')


class TestSimilarProductFinder:

    def test_find(self, product_foo, product_bar):
        result = SimilarProductFinder([product_foo, product_bar]).find('foo')
        assert len(result) == 1
        assert result[0].product.id == product_foo.id
        assert result[0].confidence == 1
