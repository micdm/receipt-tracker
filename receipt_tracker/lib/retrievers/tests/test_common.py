from receipt_tracker.lib.retrievers import ReceiptRetriever, get_receipt_retriever


def test_get_receipt_retriever():
    result = get_receipt_retriever()
    assert isinstance(result, ReceiptRetriever)
