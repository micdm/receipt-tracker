from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest import fixture

from receipt_tracker.models import User
from receipt_tracker.repositories import product_repository

pytestmark = pytest.mark.django_db


@fixture
def staff_user(mixer):
    return mixer.blend(User, is_staff=True, is_superuser=True)


@fixture
def admin_client(client, staff_user):
    client.force_login(staff_user)
    return client


class TestProductAdmin:

    def test_changelist(self, admin_client, product):
        response = admin_client.get(reverse('admin:receipt_tracker_product_changelist'))
        assert response.status_code == HTTPStatus.OK

    def test_change_if_food(self, mocker, admin_client, product):
        mocker.patch.object(product_repository, 'set_non_food')
        response = admin_client.post(reverse('admin:receipt_tracker_product_change', args=(product.id,)), {
            'make_non_food': True,
            '_save': 'foo',
            'foodproduct-TOTAL_FORMS': 0,
            'foodproduct-INITIAL_FORMS': 0,
            'nonfoodproduct-TOTAL_FORMS': 0,
            'nonfoodproduct-INITIAL_FORMS': 0,
        })
        assert response.status_code == HTTPStatus.FOUND
        assert product_repository.set_non_food.called
