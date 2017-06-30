from django.test import TestCase

from main.views import AddReceiptView


class AddReceiptViewTest(TestCase):

    def test_get_receipt_params_from_qr(self):
        result = AddReceiptView()._get_receipt_params_from_qr("t=20170615T141100&s=67.20&fn=8710000100036875&i=78337&fp=255743793&n=1")
        self.assertTupleEqual(result, ("8710000100036875", "78337", "255743793", "67.20"))
