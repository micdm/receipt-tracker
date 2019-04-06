from datetime import datetime
from decimal import Decimal
from logging import getLogger
from typing import Callable, List, Optional

from receipt_tracker.errors import BadParameter
from receipt_tracker.lib import ReceiptParams

logger = getLogger(__name__)


def decode(text: str) -> Optional[ReceiptParams]:
    try:
        parts = [part.split('=', 1) for part in text.split('&')]
        return ReceiptParams(
            _get_field(parts, 'fn', int),
            _get_field(parts, 'i', int),
            _get_field(parts, 'fp', int),
            _get_field(parts, 't', lambda value: datetime.strptime(value, '%Y%m%dT%H%M%S')),
            _get_field(parts, 's', Decimal),
        )
    except Exception as e:
        logger.warning('Cannot parse QR code: %s', e)
        return None


def _get_field(parts: List[List[str]], name: str, mapper: Callable):
    for key, value in parts:
        if key != name:
            continue
        try:
            return mapper(value)
        except Exception as e:
            logger.debug('Cannot parse field %s: %s', name, e)
            raise BadParameter(f'cannot parse field "{name}"')
    raise BadParameter(f'no field "{name}" found')
