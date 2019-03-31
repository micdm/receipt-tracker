import json
import time
from datetime import datetime
from http import HTTPStatus

import requests
from pytest import fixture, raises

from receipt_tracker.lib.retrievers import BadResponse
from receipt_tracker.lib.retrievers.nalog_ru import NalogRuReceiptRetriever
from receipt_tracker.lib.retrievers.tests import get_file_content


@fixture
def good_response(mocker):
    response = mocker.MagicMock()
    response.status_code = HTTPStatus.OK
    response.json.return_value = json.loads(get_file_content('nalog_ru_receipt_found.json'))
    return response


@fixture
def no_content_response(mocker):
    response = mocker.MagicMock()
    response.status_code = HTTPStatus.NO_CONTENT
    return response


@fixture
def accepted_response(mocker):
    response = mocker.MagicMock()
    response.status_code = HTTPStatus.ACCEPTED
    return response


class TestNalogRuReceiptRetriever:

    def test_get_receipt_if_cannot_check_receipt(self, mocker, receipt_params, bad_response):
        mocker.patch.object(requests, 'get', return_value=bad_response)
        with raises(BadResponse):
            NalogRuReceiptRetriever().get_receipt(receipt_params)

    def test_get_receipt_if_accepted_response(self, mocker, receipt_params, no_content_response, accepted_response):
        mocker.patch.object(NalogRuReceiptRetriever, 'MAX_TRIES', 2)
        mocker.patch.object(requests, 'get', side_effect=[no_content_response, accepted_response, accepted_response])
        mocker.patch.object(time, 'sleep')
        with raises(BadResponse):
            NalogRuReceiptRetriever().get_receipt(receipt_params)

    def test_get_receipt_if_bad_response(self, mocker, receipt_params, no_content_response, bad_response):
        mocker.patch.object(requests, 'get', side_effect=[no_content_response, bad_response])
        mocker.patch.object(time, 'sleep')
        with raises(BadResponse):
            NalogRuReceiptRetriever().get_receipt(receipt_params)

    def test_get_receipt_if_good_response(self, mocker, receipt_params, no_content_response, good_response):
        mocker.patch.object(requests, 'get', side_effect=[no_content_response, good_response])
        result = NalogRuReceiptRetriever().get_receipt(receipt_params)

        assert result.fiscal_drive_number == '9288000100020178'
        assert result.fiscal_document_number == '106462'
        assert result.fiscal_sign == '1984555575'
        assert result.seller_name == 'ООО "Спар-Томск"'
        assert result.seller_individual_number == '7017326645'
        assert result.created == datetime(2019, 2, 25, 20, 25)

        assert len(result.items) == 1

        assert result.items[0].price == '38.8'
        assert result.items[0].total == '38.8'
        assert result.items[0].name == 'Бифидок Деревенское молочко 2,5% 0,5л т/п/20'
        assert result.items[0].quantity == '1'
