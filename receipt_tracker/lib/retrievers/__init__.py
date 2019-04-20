from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from receipt_tracker.lib import ReceiptParams


@dataclass(frozen=True)
class ParsedReceipt:

    fiscal_drive_number: str
    fiscal_document_number: str
    fiscal_sign: str
    seller_name: str
    seller_individual_number: str
    created: datetime
    items: List['ParsedReceiptItem']


@dataclass(frozen=True)
class ParsedReceiptItem:

    name: str
    quantity: Decimal
    price: Decimal
    total: Decimal


class ReceiptRetriever(ABC):

    @abstractmethod
    def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
        raise NotImplementedError()


class BadResponse(Exception):
    pass


def get_receipt_retriever() -> ReceiptRetriever:
    from receipt_tracker.lib.retrievers.nalog_ru import NalogRuReceiptRetriever
    return NalogRuReceiptRetriever()


def get_available_receipt_retrievers() -> List[ReceiptRetriever]:
    from receipt_tracker.lib.retrievers.nalog_ru import NalogRuReceiptRetriever
    return [
        NalogRuReceiptRetriever(),
    ]
