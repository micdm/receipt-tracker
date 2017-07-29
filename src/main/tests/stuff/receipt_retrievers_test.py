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
            'fiscal_drive_number': '8710000100688395',
            'fiscal_document_number': '29324',
            'fiscal_sign': '2745981095',
            'seller_name': 'ООО "Спар-Томск"',
            'seller_individual_number': '7017326645',
            'created': datetime(2017, 7, 29, 11, 19),
            'items': (
                {'price': '43.60', 'total': '130.80', 'quantity': '3', 'name': 'Мороженое Пломбир на йогурте к'},
                {'price': '16.70', 'total': '16.70', 'quantity': '1', 'name': 'Приправа ТРАПЕЗА Лавровый лист'},
                {'price': '75.80', 'total': '75.80', 'quantity': '1', 'name': 'Квас ЖИТНИЦА 1,5л Деревенский'},
                {'price': '26.90', 'total': '26.90', 'quantity': '1', 'name': 'Хлеб Бородинский 400г/Лама'},
                {'price': '30.70', 'total': '30.70', 'quantity': '1', 'name': 'Сухарики Не только Для своих Б'},
            )
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
