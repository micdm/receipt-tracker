from datetime import datetime
from decimal import Decimal

import pytest
from pytest import fixture

from receipt_tracker import tasks
from receipt_tracker.lib.retrievers import ParsedReceipt, ParsedReceiptItem
from receipt_tracker.repositories import receipt_repository
from receipt_tracker.tasks import add_receipt

pytestmark = pytest.mark.django_db


@fixture
def receipt_params():
    return {
        'fiscal_drive_number': '1',
        'fiscal_document_number': '1',
        'fiscal_sign': '1',
        'created': '2019-04-06T09:57:56.674673',
        'amount': '1.5',
    }


@fixture
def parsed_receipt():
    return ParsedReceipt('1', '2', '3', 'foo', '4', datetime.utcnow(), [
        ParsedReceiptItem('bar', Decimal(100), Decimal(200), Decimal(300)),
    ])


@fixture
def failed_receipt_retriever(mocker):
    mock = mocker.Mock()
    mock.get_receipt.side_effect = Exception
    mocker.patch.object(tasks, 'get_receipt_retriever', return_value=mock)
    return mock


@fixture
def silent_receipt_retriever(mocker):
    mock = mocker.Mock()
    mock.get_receipt.return_value = None
    mocker.patch.object(tasks, 'get_receipt_retriever', return_value=mock)
    return mock


@fixture
def successful_receipt_retriever(mocker, parsed_receipt):
    mock = mocker.Mock()
    mock.get_receipt.return_value = parsed_receipt
    mocker.patch.object(tasks, 'get_receipt_retriever', return_value=mock)
    return mock


def test_add_receipt_if_retriever_failed(mocker, receipt_params, failed_receipt_retriever):
    mock = mocker.patch.object(add_receipt, 'retry')
    add_receipt(1, receipt_params)
    assert mock.called


def test_add_receipt_if_retriever_silent(mocker, receipt_params, silent_receipt_retriever):
    mock = mocker.patch.object(add_receipt, 'retry')
    add_receipt(1, receipt_params)
    assert mock.called


def test_add_receipt_if_retriever_successful(mocker, receipt_params, successful_receipt_retriever,
                                             parsed_receipt, user):
    add_receipt(user.id, receipt_params)

    receipts = receipt_repository.get_by_buyer_id(user.id)
    assert len(receipts) == 1

    receipt = receipts[0]
    assert str(receipt.seller.individual_number) == parsed_receipt.seller_individual_number
    assert len(receipt.items) == 1

    receipt_item = receipt.items[0]
    assert receipt_item.product_alias.name == parsed_receipt.items[0].name
    assert receipt_item.price == parsed_receipt.items[0].price
