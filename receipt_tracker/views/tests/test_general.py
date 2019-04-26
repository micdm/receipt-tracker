from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest import fixture

from receipt_tracker import tasks
from receipt_tracker.lib import ReceiptParams, qr_code
from receipt_tracker.repositories import product_repository, receipt_item_repository, receipt_repository

pytestmark = pytest.mark.django_db


class TestIndexView:

    def test(self, mocker, guest_client, receipt_item):
        mocker.patch.object(receipt_item_repository, 'get_last', return_value=[receipt_item])
        response = guest_client.get(reverse('index'))
        assert response.status_code == HTTPStatus.OK


class TestAddReceiptView:

    @fixture
    def receipt_params(self):
        return ReceiptParams('1', '1', '1', datetime.utcnow(), Decimal(1))

    def test_get(self, authorized_client):
        response = authorized_client.get(reverse('add-receipt'))
        assert response.status_code == HTTPStatus.OK

    def test_post_if_bad_qr_content_provided(self, mocker, authorized_client):
        mocker.patch.object(qr_code, 'decode', return_value=None)
        response = authorized_client.post(reverse('add-receipt'), {
            'text': 'foo',
        })
        assert response.status_code == HTTPStatus.OK

    def test_post_if_receipt_already_exists(self, mocker, authorized_client, receipt_params):
        mocker.patch.object(qr_code, 'decode', return_value=receipt_params)
        mocker.patch.object(receipt_repository, 'is_exist', return_value=True)
        response = authorized_client.post(reverse('add-receipt'), {
            'text': 'foo',
        })
        assert response.status_code == HTTPStatus.OK

    def test_post(self, mocker, authorized_client, receipt_params):
        mocker.patch.object(qr_code, 'decode', return_value=receipt_params)
        mocker.patch.object(receipt_repository, 'is_exist', return_value=False)
        mocker.patch.object(tasks, 'add_receipt')
        response = authorized_client.post(reverse('add-receipt'), {
            'text': 'foo',
        })
        assert response.status_code == HTTPStatus.FOUND


class TestReceiptAddedView:

    def test(self, guest_client):
        response = guest_client.get(reverse('receipt-added'))
        assert response.status_code == HTTPStatus.OK


class TestProductsView:

    def test(self, mocker, guest_client, product, receipt_item):
        mocker.patch.object(product_repository, 'get_all', return_value=[product])
        response = guest_client.get(reverse('products'))
        assert response.status_code == HTTPStatus.OK


class TestProductView:

    def test_if_get_and_product_not_found(self, mocker, guest_client):
        mocker.patch.object(product_repository, 'get_by_id', return_value=None)
        response = guest_client.get(reverse('product', args=(1,)))
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_if_get_and_product_found(self, mocker, guest_client, product, food_product, receipt_item):
        mocker.patch.object(product_repository, 'get_by_id', return_value=product)
        mocker.patch.object(receipt_item_repository, 'is_exist_by_product_id_and_buyer_id', return_value=False)
        mocker.patch.object(receipt_item_repository, 'get_by_product_id', return_value=[receipt_item])
        response = guest_client.get(reverse('product', args=(product.id,)))
        assert response.status_code == HTTPStatus.OK

    def test_if_get_and_non_food_product_found(self, mocker, guest_client, product, non_food_product, receipt_item):
        mocker.patch.object(product_repository, 'get_by_id', return_value=product)
        mocker.patch.object(receipt_item_repository, 'is_exist_by_product_id_and_buyer_id', return_value=False)
        mocker.patch.object(receipt_item_repository, 'get_by_product_id', return_value=[receipt_item])
        response = guest_client.get(reverse('product', args=(product.id,)))
        assert response.status_code == HTTPStatus.OK

    def test_if_post_and_edit_not_allowed(self, mocker, guest_client, product):
        mocker.patch.object(product_repository, 'get_by_id', return_value=product)
        mocker.patch.object(receipt_item_repository, 'is_exist_by_product_id_and_buyer_id', return_value=False)
        response = guest_client.post(reverse('product', args=(product.id,)))
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_if_post_and_product_not_updated(self, mocker, authorized_client, product, food_product, receipt_item):
        mocker.patch.object(product_repository, 'get_by_id', return_value=product)
        mocker.patch.object(receipt_item_repository, 'is_exist_by_product_id_and_buyer_id', return_value=True)
        mocker.patch.object(product_repository, 'set_barcode', return_value=None)
        mocker.patch.object(receipt_item_repository, 'get_by_product_id', return_value=[receipt_item])
        response = authorized_client.post(reverse('product', args=(product.id,)), {
            'barcode': '1',
        })
        assert response.status_code == HTTPStatus.OK

    def test_if_post_and_product_updated(self, mocker, authorized_client, product, product_with_barcode,
                                         food_product, receipt_item):
        mocker.patch.object(product_repository, 'get_by_id', return_value=product)
        mocker.patch.object(receipt_item_repository, 'is_exist_by_product_id_and_buyer_id', return_value=True)
        mocker.patch.object(product_repository, 'set_barcode', return_value=product_with_barcode.id)
        mocker.patch.object(receipt_item_repository, 'get_by_product_id', return_value=[receipt_item])
        response = authorized_client.post(reverse('product', args=(product.id,)), {
            'barcode': product_with_barcode.barcode,
        })
        assert response.status_code == HTTPStatus.FOUND
