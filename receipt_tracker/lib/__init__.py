from _pydecimal import Decimal
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReceiptParams:

    fiscal_drive_number: int
    fiscal_document_number: int
    fiscal_sign: int
    created: datetime
    amount: Decimal
