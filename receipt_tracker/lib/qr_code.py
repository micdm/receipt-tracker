import re
from typing import Tuple

FISCAL_DRIVE_NUMBER_PATTERN = re.compile(r'fn=(\d+)')
FISCAL_DOCUMENT_NUMBER_PATTERN = re.compile(r'i=(\d+)')
FISCAL_SIGN_PATTERN = re.compile(r'fp=(\d+)')
TOTAL_SUM_PATTERN = re.compile(r's=([\d.]+)')


def decode(text: str) -> Tuple[str, str, str, str]:
    try:
        return tuple(pattern.search(text).group(1) for pattern in (
            FISCAL_DRIVE_NUMBER_PATTERN,
            FISCAL_DOCUMENT_NUMBER_PATTERN,
            FISCAL_SIGN_PATTERN,
            TOTAL_SUM_PATTERN,
        ))
    except:
        raise Exception('cannot parse QR code')
