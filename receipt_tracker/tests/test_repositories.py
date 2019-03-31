from datetime import datetime, timedelta

import pytest
from pytest import fixture

from receipt_tracker.models import Product, Receipt, ReceiptItem, User
from receipt_tracker.repositories import product_repository, receipt_item_repository, receipt_repository

pytestmark = pytest.mark.django_db


class TestProductRepository:

    @fixture
    def another_product(self, mixer):
        return mixer.blend(Product)

    def test_get_all(self, product, another_product):
        result = product_repository.get_all()
        assert len(result) == 2
        assert result[0].id == product.id
        assert result[1].id == another_product.id

    def test_get_by_id_if_not_found(self):
        result = product_repository.get_by_id(1)
        assert result is None

    def test_get_by_id_if_found(self, product):
        result = product_repository.get_by_id(product.id)
        assert result.id == product.id

    def test_set_barcode_if_original_product_not_found(self, product):
        result = product_repository.set_barcode(product.id, 1)
        assert result is None

    def test_set_barcode_if_original_product_found(self, product, product_alias, product_with_barcode):
        result = product_repository.set_barcode(product.id, product_with_barcode.barcode)
        assert result == product_with_barcode.id

        product_alias.refresh_from_db()
        assert product_alias.product.id == product_with_barcode.id

    def test_set_non_food_if_non_food(self, product, non_food_product):
        result = product_repository.set_non_food(product.id)
        assert not result

    def test_set_non_food_if_food(self, product, food_product):
        result = product_repository.set_non_food(product.id)
        assert result

        product.refresh_from_db()
        assert product.is_non_food


class TestReceiptRepository:

    @fixture
    def receipt(self, mixer, user):
        return mixer.blend(Receipt, buyer=user, created=datetime.utcnow() - timedelta(days=1))

    @fixture
    def another_receipt(self, mixer, user):
        return mixer.blend(Receipt, buyer=user, created=datetime.utcnow())

    @fixture
    def old_receipt(self, mixer, user):
        return mixer.blend(Receipt, buyer=user, created=datetime.utcnow() - timedelta(days=100))

    @fixture
    def another_user(self, mixer):
        return mixer.blend(User)

    @fixture
    def another_buyer_receipt(self, mixer, another_user):
        return mixer.blend(Receipt, buyer=another_user, created=datetime.utcnow())

    def test_get_last_by_buyer_id(self, user, receipt, another_receipt, old_receipt, another_buyer_receipt):
        result = receipt_repository.get_last_by_buyer_id(user.id)
        assert len(result) == 2
        assert result[0].id == another_receipt.id
        assert result[1].id == receipt.id


class TestReceiptItemRepository:

    @fixture
    def product(self, mixer):
        return mixer.blend(Product)

    @fixture
    def another_product(self, mixer):
        return mixer.blend(Product)

    @fixture
    def receipt(self, mixer, user):
        return mixer.blend(Receipt, buyer=user, created=datetime.utcnow())

    @fixture
    def old_receipt(self, mixer):
        return mixer.blend(Receipt, created=datetime.utcnow() - timedelta(days=1))

    @fixture
    def receipt_item(self, mixer, product, receipt):
        return mixer.blend(ReceiptItem, receipt=receipt, product_alias__product=product)

    @fixture
    def old_receipt_item(self, mixer, another_product, old_receipt):
        return mixer.blend(ReceiptItem, receipt=old_receipt, product_alias__product=another_product)

    def test_get_last(self, receipt_item, old_receipt_item):
        result = receipt_item_repository.get_last()
        assert len(result) == 2
        assert result[0].id == receipt_item.id
        assert result[1].id == old_receipt_item.id

    def test_get_last_by_buyer_id(self, user, receipt_item, old_receipt_item):
        result = receipt_item_repository.get_last_by_buyer_id(user.id)
        assert len(result) == 1
        assert result[0].id == receipt_item.id

    def test_get_by_product_id(self, product, receipt_item, old_receipt_item):
        result = receipt_item_repository.get_by_product_id(product.id)
        assert len(result) == 1
        assert result[0].id == receipt_item.id

    def test_is_exist_by_product_id_and_buyer_id_if_exists(self, user, product, receipt_item):
        result = receipt_item_repository.is_exist_by_product_id_and_buyer_id(product.id, user.id)
        assert result

    def test_is_exist_by_product_id_and_buyer_id_if_not_exists(self, user, product, old_receipt_item):
        result = receipt_item_repository.is_exist_by_product_id_and_buyer_id(product.id, user.id)
        assert not result

