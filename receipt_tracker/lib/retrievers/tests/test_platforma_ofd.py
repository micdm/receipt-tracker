from datetime import datetime

import requests
from pytest import raises

from receipt_tracker.lib.retrievers import BadResponse
from receipt_tracker.lib.retrievers.platforma_ofd import Parser, PlatformaOfdOperatorReceiptRetriever
from receipt_tracker.lib.retrievers.tests import get_file_content


class TestPlatformaOfdOperatorReceiptRetriever:

    def test_get_receipt_if_bad_response(self, mocker, receipt_params, bad_response):
        mocker.patch.object(requests, 'get', return_value=bad_response)
        with raises(BadResponse):
            PlatformaOfdOperatorReceiptRetriever().get_receipt(receipt_params)

    def test_get_receipt(self, mocker, receipt_params, good_response):
        mocker.patch.object(requests, 'get', return_value=good_response)
        mocker.patch.object(Parser, 'parse', return_value=True)
        result = PlatformaOfdOperatorReceiptRetriever().get_receipt(receipt_params)
        assert result


class TestParser:

    def test_parse_if_receipt_found(self):
        result = Parser().parse(get_file_content('platforma_ofd_receipt_found.html'))

        assert result.fiscal_drive_number == '8710000100688395'
        assert result.fiscal_document_number == '29324'
        assert result.fiscal_sign == '2745981095'
        assert result.seller_name == 'ООО "Спар-Томск"'
        assert result.seller_individual_number == '7017326645'
        assert result.created == datetime(2017, 7, 29, 11, 19)

        assert len(result.items) == 5

        assert result.items[0].price == '43.60'
        assert result.items[0].total == '130.80'
        assert result.items[0].name == 'Мороженое Пломбир на йогурте к'
        assert result.items[0].quantity == '3'

        assert result.items[2].price == '75.80'
        assert result.items[2].total == '75.80'
        assert result.items[2].name == 'Квас ЖИТНИЦА 1,5л Деревенский'
        assert result.items[2].quantity == '1'

        assert result.items[4].price == '30.70'
        assert result.items[4].total == '30.70'
        assert result.items[4].name == 'Сухарики Не только Для своих Б'
        assert result.items[4].quantity == '1'

    def test_parse_if_receipt_found_with_no_barcodes(self):
        result = Parser().parse(get_file_content('platforma_ofd_receipt_found_with_no_barcodes.html'))

        assert result.fiscal_drive_number == '8710000100816354'
        assert result.fiscal_document_number == '1539'
        assert result.fiscal_sign == '2964112708'
        assert result.seller_name == 'ООО "Хитэк-Сибирь"'
        assert result.seller_individual_number == '5406358004'
        assert result.created == datetime(2017, 6, 30, 12, 32)

        assert len(result.items) == 1

        assert result.items[0].price == '279.00'
        assert result.items[0].total == '279.00'
        assert result.items[0].name == '1. KAP-590  Флюид для поврежденных кончиков волос "Treatment", 6'
        assert result.items[0].quantity == '1'

    def test_parse_if_receipt_not_found(self):
        result = Parser().parse(get_file_content('platforma_ofd_receipt_not_found.html'))
        assert result is None
