from datetime import datetime
from decimal import Decimal

from receipt_tracker.lib.qr_code import decode


def test_decode():
    result = decode('t=20170615T141100&s=67.20&fn=8710000100036875&i=78337&fp=255743793&n=1')
    assert result.fiscal_drive_number == 8710000100036875
    assert result.fiscal_document_number == 78337
    assert result.fiscal_sign == 255743793
    assert result.created == datetime(2017, 6, 15, 14, 11)
    assert result.amount == Decimal('67.2')


def test_decode_if_no_field():
    result = decode('foo=bar')
    assert result is None


def test_decode_if_bad_field():
    result = decode('fn=foo')
    assert result is None
