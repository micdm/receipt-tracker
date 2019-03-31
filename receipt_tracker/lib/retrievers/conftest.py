from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

from pytest import fixture

from receipt_tracker.lib.retrievers import ReceiptParams


@fixture
def receipt_params():
    return ReceiptParams('foo', 'bar', 'baz', datetime.utcnow(), Decimal(1))


@fixture
def good_response(mocker):
    response = mocker.MagicMock()
    response.status_code = HTTPStatus.OK
    return response


@fixture
def bad_response(mocker):
    response = mocker.MagicMock()
    response.status_code = HTTPStatus.BAD_REQUEST
    return response
