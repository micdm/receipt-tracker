from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


class ReceiptParams:

    def __init__(self, fiscal_drive_number: str, fiscal_document_number: str, fiscal_sign: str,
                 created: datetime, amount: Decimal):
        self.fiscal_drive_number = fiscal_drive_number
        self.fiscal_document_number = fiscal_document_number
        self.fiscal_sign = fiscal_sign
        self.created = created
        self.amount = amount


class ParsedReceipt:

    def __init__(self, fiscal_drive_number: str, fiscal_document_number: str, fiscal_sign: str, seller_name: str,
                 seller_individual_number: str, created: datetime, items: List['ParsedReceiptItem']):
        self.fiscal_drive_number = fiscal_drive_number
        self.fiscal_document_number = fiscal_document_number
        self.fiscal_sign = fiscal_sign
        self.seller_name = seller_name
        self.seller_individual_number = seller_individual_number
        self.created = created
        self.items = items


class ParsedReceiptItem:

    def __init__(self, name: str, quantity: str, price: str, total: str):
        self.name = name
        self.quantity = quantity
        self.price = price
        self.total = total


class ReceiptRetriever(ABC):

    @abstractmethod
    def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
        raise NotImplementedError()


class BadResponse(Exception):
    pass


def get_receipt_retriever() -> ReceiptRetriever:
    from receipt_tracker.lib.retrievers.combined import CombinedReceiptRetriever
    from receipt_tracker.lib.retrievers.nalog_ru import NalogRuReceiptRetriever
    from receipt_tracker.lib.retrievers.platforma_ofd import PlatformaOfdOperatorReceiptRetriever
    from receipt_tracker.lib.retrievers.taxcom import TaxcomOperatorReceiptRetriever
    return CombinedReceiptRetriever([
        PlatformaOfdOperatorReceiptRetriever(),
        TaxcomOperatorReceiptRetriever(),
        NalogRuReceiptRetriever(),
    ])
