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
            'fiscal_drive_number': '8710000100547729',
            'fiscal_document_number': '55102',
            'fiscal_sign': '3848832309',
            'seller_name': 'ООО "Лента"',
            'seller_individual_number': '7814148471',
            'created': datetime(2017, 8, 6, 13, 8),
            'items': (
                {'total': '3.19', 'name': 'Пакет ЛЕНТА майка 9кг', 'quantity': '1', 'price': '3.19'},
                {'total': '79.29', 'name': 'Мыло DURU Soft sens календула 90гх4', 'quantity': '1', 'price': '79.29'},
                {'total': '129.99', 'name': 'З/паста SPLAT 100мл', 'quantity': '1', 'price': '129.99'},
                {'total': '21.49', 'name': 'Т/мыло DURU Soft sens грейпфрут 80г', 'quantity': '1', 'price': '21.49'},
                {'total': '427.07', 'name': 'П/ф Свинина окорок премиум б/к охл. вес', 'quantity': '1.188', 'price': '359.49'},
                {'total': '112.18', 'name': 'Конф КРАСНЫЙ ОКТЯБРЬ Мишка косол.вес.1кг', 'quantity': '0.142', 'price': '789.99'},
                {'total': '64.32', 'name': 'Конфеты TWIX Минис Имбирное печенье вес', 'quantity': '0.134', 'price': '479.99'},
                {'total': '26.59', 'name': "Мыло DURU Nature'S Treasures Мед Минд90г", 'quantity': '1', 'price': '26.59'},
                {'total': '17.29', 'name': 'Салфетки 365 ДНЕЙ 24*24см 1-сл. 100шт', 'quantity': '1', 'price': '17.29'},
                {'total': '21.49', 'name': 'Палочки НИКИТКА Кукурузные сливочные 80г', 'quantity': '1', 'price': '21.49'},
                {'total': '98.99', 'name': 'Кондиц-р д/белья LENOR Минд Масло д/ч 1л', 'quantity': '1', 'price': '98.99'},
                {'total': '22.13', 'name': 'Лук репчатый новый урожай вес 1кг', 'quantity': '0.472', 'price': '46.89'},
                {'total': '17.98', 'name': 'Томаты вес 1 кг', 'quantity': '0.316', 'price': '56.89'},
            )
        })

    def test_parse_html_if_receipt_not_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(_get_file_content('taxcom_receipt_not_found.html'))
        self.assertIsNone(result)
