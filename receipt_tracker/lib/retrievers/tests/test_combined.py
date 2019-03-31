from typing import Optional

from pytest import fixture

from receipt_tracker.lib.retrievers import ParsedReceipt, ReceiptParams, ReceiptRetriever
from receipt_tracker.lib.retrievers.combined import CombinedReceiptRetriever


@fixture
def successful_retriever():
    class CustomReceiptRetriever(ReceiptRetriever):
        def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
            return True
    return CustomReceiptRetriever()


@fixture
def failing_retriever():
    class CustomReceiptRetriever(ReceiptRetriever):
        def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
            raise Exception()
    return CustomReceiptRetriever()


class TestCombinedReceiptRetriever:

    def test_get_receipt_if_cannot_retrieve(self, receipt_params, failing_retriever):
        result = CombinedReceiptRetriever([
            failing_retriever,
        ]).get_receipt(receipt_params)
        assert result is None

    def test_get_receipt(self, receipt_params, successful_retriever, failing_retriever):
        result = CombinedReceiptRetriever([
            failing_retriever,
            successful_retriever,
        ]).get_receipt(receipt_params)
        assert result
