from datetime import datetime
from http import HTTPStatus

import pytest
from django.test import TestCase
from django.urls import reverse
from pytest import fixture

from receipt_tracker.models import Product, ProductAlias, Receipt, ReceiptItem, FoodProduct
from receipt_tracker.repositories import receipt_item_repository, product_repository
from receipt_tracker.views import AddReceiptView

pytestmark = pytest.mark.django_db


@fixture
def receipt(mixer, user):
    return mixer.blend(Receipt, buyer=user, created=datetime.utcnow())


@fixture
def product(mixer):
    return mixer.blend(Product)


@fixture
def food_product(mixer, product):
    return mixer.blend(FoodProduct, product=product)


@fixture
def product_alias(mixer, product):
    return mixer.blend(ProductAlias, product=product)


@fixture
def receipt_item(mixer, receipt, product_alias):
    return mixer.blend(ReceiptItem, receipt=receipt, product_alias=product_alias)


class TestIndexView:

    def test(self, guest_client, receipt_item):
        response = guest_client.get(reverse('index'))
        assert response.status_code == HTTPStatus.OK


class TestAddReceiptView:

    def test_get(self, authorized_client):
        response = authorized_client.get(reverse('add-receipt'))
        assert response.status_code == HTTPStatus.OK

    def test_post_if_bad_qr_content_provided(self, authorized_client):
        response = authorized_client.post(reverse('add-receipt'), {
            'qr': True,
            'text': 'foobar',
        })
        assert response.status_code == HTTPStatus.OK

    def test_post_if_qr_content_provided(self, authorized_client):
        response = authorized_client.post(reverse('add-receipt'), {
            'qr': '1',
            'text': 't=20170615T141100&s=67.20&fn=8710000100036875&i=78337&fp=255743793&n=1',
        })
        assert response.status_code == HTTPStatus.FOUND

    def test_post_if_manual_content_provided(self, authorized_client):
        response = authorized_client.post(reverse('add-receipt'), {
            'manual': '1',
            'fiscal_drive_number': '1',
            'fiscal_document_number': '2',
            'fiscal_sign': '3',
            'total_sum': '4',
        })
        assert response.status_code == HTTPStatus.FOUND


class TestReceiptAddedView:

    def test(self, guest_client):
        response = guest_client.get(reverse('receipt-added'))
        assert response.status_code == HTTPStatus.OK


class TestProductsView:

    def test(self, guest_client, product, receipt_item):
        response = guest_client.get(reverse('products'))
        assert response.status_code == HTTPStatus.OK


class TestProductView:

    def test_if_get(self, guest_client, product, receipt_item):
        response = guest_client.get(reverse('product', args=(product.id,)))
        assert response.status_code == HTTPStatus.OK

    def test_if_post_and_product_not_found(self, authorized_client):
        response = authorized_client.post(reverse('product', args=(1,)))
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_if_post_and_product_updated(self, authorized_client, product, receipt_item):
        response = authorized_client.post(reverse('product', args=(product.id,)), {
            'barcode': '1'
        })
        assert response.status_code == HTTPStatus.FOUND


class TestValueReportView:

    def test(self, authorized_client, receipt_item):
        response = authorized_client.get(reverse('value-report'))
        assert response.status_code == HTTPStatus.OK


class TestTopReportView:

    def test(self, authorized_client, receipt_item):
        response = authorized_client.get(reverse('top-report'))
        assert response.status_code == HTTPStatus.OK


class TestSummaryReportView:

    def test(self, authorized_client, food_product, receipt_item):
        response = authorized_client.get(reverse('summary-report'))
        assert response.status_code == HTTPStatus.OK
