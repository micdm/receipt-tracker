from datetime import datetime
import os.path

from django.test import TestCase

from main.stuff.receipt_retrievers import _PlatformaOfdOperatorReceiptRetriever, _TaxcomOperatorReceiptRetriever


def _get_file_content(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()


class PlatformaOfdOperatorReceiptRetrieverTest(TestCase):

    def test_parse_html_if_receipt_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(_get_file_content('platforma_ofd_receipt_found.html'))
        self.assertDictEqual(result, {
            'fiscal_drive_number': '8710000100816354',
            'fiscal_document_number': '1539',
            'fiscal_sign': '2964112708',
            'seller_name': 'ООО "Хитэк-Сибирь"',
            'seller_individual_number': '5406358004',
            'created': datetime(2017, 6, 30, 12, 32),
            'items': ({'price': '279.00', 'total': '279.00', 'name': '1. KAP-590  Флюид для поврежденных кончиков волос "Treatment", 6', 'quantity': '1'},)
        })

    def test_parse_html_if_receipt_not_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(_get_file_content('platforma_ofd_receipt_not_found.html'))
        self.assertIsNone(result)


class TaxcomOperatorReceiptRetrieverTest(TestCase):

    def test_parse_html_if_receipt_found(self):
        result = _TaxcomOperatorReceiptRetriever()._parse_html(_get_file_content('taxcom_receipt_found.html'))
        self.assertDictEqual(result, {
            'fiscal_drive_number': '8710000100547789',
            'fiscal_document_number': '2601',
            'fiscal_sign': '1759143434',
            'seller_name': 'ООО "Лента"',
            'seller_individual_number': '7814148471',
            'created': datetime(2017, 6, 23, 13, 39),
            'items': (
                {'total': '937.80', 'quantity': '20', 'price': '46.89', 'name': 'Пиво HEINEKEN 4,8% 0.5L ст'},
                {'total': '6.49', 'quantity': '1', 'price': '6.49', 'name': 'Пакет ЛЕНТА майка 12кг'},
                {'total': '1289.00', 'quantity': '1', 'price': '1289.00', 'name': 'Коньяк СТАРЕЙШИНА Российский 5лет 1L'},
                {'total': '699.98', 'quantity': '2', 'price': '349.99', 'name': 'ВиноLaFermeDeCerraiМуск.бел.п/сл.Фр.0.75'},
                {'total': '1319.99', 'quantity': '1', 'price': '1319.99', 'name': 'Текила JOSE CUERVO Хосе Куэр Сильвер 0.7'},
                {'total': '30.94', 'quantity': '0.238', 'price': '129.99', 'name': 'Чеснок вес 1кг'},
                {'total': '60.30', 'quantity': '0.331', 'price': '182.17', 'name': 'Пирог Лента с луком и яйцом вес'}
            )
        })

    def test_parse_html_if_receipt_not_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(_get_file_content('taxcom_receipt_not_found.html'))
        self.assertIsNone(result)
