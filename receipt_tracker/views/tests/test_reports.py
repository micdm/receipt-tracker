from http import HTTPStatus

import pytest
from django.urls import reverse

from receipt_tracker.repositories import receipt_item_repository, receipt_repository

pytestmark = pytest.mark.django_db


class TestValueReportView:

    def test(self, mocker, authorized_client, receipt, receipt_item):
        mocker.patch.object(receipt_repository, 'get_last_by_buyer_id', return_value=[receipt])
        response = authorized_client.get(reverse('value-report'))
        assert response.status_code == HTTPStatus.OK


class TestTopReportView:

    def test_if_food(self, mocker, authorized_client, food_product, receipt_item):
        mocker.patch.object(receipt_item_repository, 'get_last_by_buyer_id', return_value=[receipt_item])
        response = authorized_client.get(reverse('top-report'))
        assert response.status_code == HTTPStatus.OK

    def test_if_non_food(self, mocker, authorized_client, non_food_product, receipt_item):
        mocker.patch.object(receipt_item_repository, 'get_last_by_buyer_id', return_value=[receipt_item])
        response = authorized_client.get(reverse('top-report'))
        assert response.status_code == HTTPStatus.OK


class TestSummaryReportView:

    def test_if_food(self, mocker, authorized_client, food_product, receipt_item):
        mocker.patch.object(receipt_item_repository, 'get_last_by_buyer_id', return_value=[receipt_item])
        response = authorized_client.get(reverse('summary-report'))
        assert response.status_code == HTTPStatus.OK

    def test_if_non_food(self, mocker, authorized_client, non_food_product, receipt_item):
        mocker.patch.object(receipt_item_repository, 'get_last_by_buyer_id', return_value=[receipt_item])
        response = authorized_client.get(reverse('summary-report'))
        assert response.status_code == HTTPStatus.OK

    def test_if_food_and_sorting_key_set(self, mocker, authorized_client, food_product, receipt_item):
        mocker.patch.object(receipt_item_repository, 'get_last_by_buyer_id', return_value=[receipt_item])
        response = authorized_client.get(f'{reverse("summary-report")}?sort=protein')
        assert response.status_code == HTTPStatus.OK
