from receipt_tracker.lib.retrievers import ReceiptRetriever, get_available_receipt_retrievers, get_receipt_retriever


def test_get_receipt_retriever():
    result = get_receipt_retriever()
    assert isinstance(result, ReceiptRetriever)


def test_get_available_receipt_retrievers():
    result = get_available_receipt_retrievers()
    assert isinstance(result, list)
    assert isinstance(result[0], ReceiptRetriever)
