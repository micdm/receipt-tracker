import os.path

from django.test import TestCase

from main.stuff.receipt_retrievers import _PlatformaOfdOperatorReceiptRetriever


class PlatformaOfdOperatorReceiptRetrieverTest(TestCase):

    def test_parse_html_if_receipt_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(self._get_file_content('receipt_found.html'))
        self.assertDictEqual(result, {
            'fiscal_drive_number': '8710000100036875',
            'fiscal_document_number': '82783',
            'fiscal_sign': '3006261485',
            'seller_name': 'ООО "Спар-Томск"',
            'seller_individual_number': '7017326645',
            'created': '2017-06-27T12:50:00',
            'items': (
                {'barcode': '79044', 'name': 'Сок Сады Придонья 1л мультифру', 'total': '74.90', 'price': '74.90', 'quantity': '1'},
                {'barcode': '357915', 'name': 'Батончик мюсли Фитоидея яблоко', 'total': '17.70', 'price': '17.70', 'quantity': '1'},
                {'barcode': '357916', 'name': 'Батончик мюсли Фитоидея черник', 'total': '35.40', 'price': '17.70', 'quantity': '2'},
                {'barcode': '368170', 'name': 'Салат из спаржи, 1уп/150 гр/СП', 'total': '69.90', 'price': '69.90', 'quantity': '1'},
                {'barcode': '343650', 'name': 'Шницель куриный,капуста тушена', 'total': '79.90', 'price': '79.90', 'quantity': '1'}
            ),
        })

    def test_parse_html_if_receipt_not_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(self._get_file_content('receipt_not_found.html'))
        self.assertIsNone(result)

    def _get_file_content(self, name):
        return open(os.path.join(os.path.dirname(__file__), name)).read()
