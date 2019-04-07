from _pydecimal import Decimal
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReceiptParams:

    fiscal_drive_number: str
    fiscal_document_number: str
    fiscal_sign: str
    created: datetime
    amount: Decimal
