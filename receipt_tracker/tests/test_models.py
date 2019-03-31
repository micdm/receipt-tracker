import pytest

from receipt_tracker.models import Product

pytestmark = pytest.mark.django_db


class TestSeller:

    def test_str(self, seller):
        result = str(seller)
        assert result


class TestProduct:

    def test_str(self, product):
        result = str(product)
        assert result

    def test_name_if_user_friendly_name_set(self, mocker, product):
        with mocker.patch.object(product, 'user_friendly_name'):
            result = str(product)
        assert result

    def test_name_if_no_aliases(self, mocker, product):
        with mocker.patch.object(Product, 'aliases', return_value=[]):
            result = str(product)
        assert result


class TestFoodProduct:

    def test_str(self, food_product):
        result = str(food_product)
        assert result


class TestNonFoodProduct:

    def test_str(self, non_food_product):
        result = str(non_food_product)
        assert result


class TestProductAlias:

    def test_str(self, product_alias):
        result = str(product_alias)
        assert result


class TestReceipt:

    def test_str(self, receipt):
        result = str(receipt)
        assert result


class TestReceiptItem:

    def test_str(self, receipt_item):
        result = str(receipt_item)
        assert result
