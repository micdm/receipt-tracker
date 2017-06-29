import os.path

from django.test import TestCase

from main.stuff.receipt_retrievers import _PlatformaOfdOperatorReceiptRetriever


class PlatformaOfdOperatorReceiptRetrieverTest(TestCase):

    def test_parse_html_if_receipt_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(self._get_file_content('receipt_found.html'))
        self.assertDictEqual(result, {
            'document': {
                'receipt': {
                    'user': 'ООО "Спар-Томск"',
                    'fiscalSign': '3006261485',
                    'userInn': '7017326645',
                    'items': ({'barcode': '79044', 'name': 'Сок Сады Придонья 1л мультифру', 'sum': '74.90', 'price': '74.90', 'quantity': '1'},
                              {'barcode': '357915', 'name': 'Батончик мюсли Фитоидея яблоко', 'sum': '17.70', 'price': '17.70', 'quantity': '1'},
                              {'barcode': '357916', 'name': 'Батончик мюсли Фитоидея черник', 'sum': '35.40', 'price': '17.70', 'quantity': '2'},
                              {'barcode': '368170', 'name': 'Салат из спаржи, 1уп/150 гр/СП', 'sum': '69.90', 'price': '69.90', 'quantity': '1'},
                              {'barcode': '343650', 'name': 'Шницель куриный,капуста тушена', 'sum': '79.90', 'price': '79.90', 'quantity': '1'}),
                    'fiscalDocumentNumber': '82783',
                    'dateTime': '2017-06-27T12:50:00',
                    'fiscalDriveNumber': '8710000100036875'
                }
            }
        })

    def test_parse_html_if_receipt_not_found(self):
        result = _PlatformaOfdOperatorReceiptRetriever()._parse_html(self._get_file_content('receipt_not_found.html'))
        self.assertIsNone(result)

    def _get_file_content(self, name):
        return open(os.path.join(os.path.dirname(__file__), name)).read()
