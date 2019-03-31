import pytest

from receipt_tracker.models import Product, ReceiptItem

pytestmark = pytest.mark.django_db


class TestSeller:

    def test_str(self, seller):
        result = str(seller)
        assert result

    def test_name_if_user_friendly_name_set(self, mocker, seller):
        mocker.patch.object(seller, 'user_friendly_name')
        result = seller.name
        assert result

    def test_name(self, mocker, seller):
        mocker.patch.object(seller, 'user_friendly_name', None)
        result = seller.name
        assert result


class TestProduct:

    def test_str(self, product):
        result = str(product)
        assert result

    def test_name_if_user_friendly_name_set(self, mocker, product):
        mocker.patch.object(product, 'user_friendly_name')
        result = product.name
        assert result

    def test_name_if_no_aliases(self, mocker, product):
        mocker.patch.object(Product, 'aliases', mocker.PropertyMock(return_value=[]))
        result = product.name
        assert result

    def test_details_if_food(self, product, food_product):
        result = product.details
        assert result == food_product

    def test_details_if_non_food(self, product, non_food_product):
        result = product.details
        assert result == non_food_product

    def test_details_if_unknown(self, product):
        result = product.details
        assert result is None


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

    def test_calories(self, mocker, receipt, receipt_item):
        mocker.patch.object(ReceiptItem, 'calories', mocker.PropertyMock(return_value=1))
        result = receipt.calories
        assert result == 1


class TestReceiptItem:

    def test_str(self, receipt_item):
        result = str(receipt_item)
        assert result
