from datetime import datetime

import requests
from pytest import raises

from receipt_tracker.lib.retrievers import BadResponse
from receipt_tracker.lib.retrievers.taxcom import Parser, TaxcomOperatorReceiptRetriever
from receipt_tracker.lib.retrievers.tests import get_file_content


class TestTaxcomOperatorReceiptRetriever:

    def test_get_receipt_if_bad_response(self, mocker, receipt_params, bad_response):
        mocker.patch.object(requests, 'get', return_value=bad_response)
        with raises(BadResponse):
            TaxcomOperatorReceiptRetriever().get_receipt(receipt_params)

    def test_get_receipt(self, mocker, receipt_params, good_response):
        mocker.patch.object(requests, 'get', return_value=good_response)
        mocker.patch.object(Parser, 'parse', return_value=True)
        result = TaxcomOperatorReceiptRetriever().get_receipt(receipt_params)
        assert result


class TestParser:

    def test_parse_if_receipt_found_v1(self):
        result = Parser().parse(get_file_content('taxcom_receipt_found_v1.html'))

        assert result.fiscal_drive_number == '8710000100547729'
        assert result.fiscal_document_number == '55102'
        assert result.fiscal_sign == '3848832309'
        assert result.seller_name == 'ООО "Лента"'
        assert result.seller_individual_number == '7814148471'
        assert result.created == datetime(2017, 8, 6, 13, 8)

        assert len(result.items) == 13

        assert result.items[0].total == '3.19'
        assert result.items[0].name == 'Пакет ЛЕНТА майка 9кг'
        assert result.items[0].quantity == '1'
        assert result.items[0].price == '3.19'

        assert result.items[7].total == '26.59'
        assert result.items[7].name == "Мыло DURU Nature'S Treasures Мед Минд90г"
        assert result.items[7].quantity == '1'
        assert result.items[7].price == '26.59'

        assert result.items[12].total == '17.98'
        assert result.items[12].name == 'Томаты вес 1 кг'
        assert result.items[12].quantity == '0.316'
        assert result.items[12].price == '56.89'

    def test_parse_if_receipt_found_v2(self):
        result = Parser().parse(get_file_content('taxcom_receipt_found_v2.html'))

        assert result.fiscal_drive_number == '8710000100548077'
        assert result.fiscal_document_number == '43119'
        assert result.fiscal_sign == '1514696382'
        assert result.seller_name == 'ООО "Лента"'
        assert result.seller_individual_number == '7814148471'
        assert result.created == datetime(2017, 10, 21, 12, 25)

        assert len(result.items) == 14

        assert result.items[0].price == '40.89'
        assert result.items[0].total == '40.89'
        assert result.items[0].name == 'Продукт к/м ДЕРЕВ МОЛ яб/б 2,5% п/п 450г'
        assert result.items[0].quantity == '1'

        assert result.items[5].price == '997.06'
        assert result.items[5].total == '190.44'
        assert result.items[5].name == 'Орехи грецкие очищ. 1 сорт вес'
        assert result.items[5].quantity == '0.191'

        assert result.items[13].price == '119.99'
        assert result.items[13].total == '119.99'
        assert result.items[13].name == 'Т/бумага FAMILIA Plus Маг цвет 2-сл.12шт'
        assert result.items[13].quantity == '1'

    def test_parse_if_receipt_not_found(self):
        result = Parser().parse(get_file_content('taxcom_receipt_not_found.html'))
        assert result is None
