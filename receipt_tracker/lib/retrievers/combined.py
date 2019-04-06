from logging import getLogger
from typing import List, Optional

from receipt_tracker.lib import ReceiptParams
from receipt_tracker.lib.retrievers import ParsedReceipt, ReceiptRetriever

logger = getLogger(__name__)


class CombinedReceiptRetriever(ReceiptRetriever):

    def __init__(self, retrievers: List[ReceiptRetriever]):
        self._retrievers = retrievers

    def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
        for retriever in self._retrievers:
            try:
                logger.debug('Retrieving receipt via %s', retriever)
                data = retriever.get_receipt(params)
                if data:
                    logger.debug('Receipt found via %s', retriever)
                    return data
            except Exception as e:
                logger.warning('Cannot retrieve receipt: %s', e)
        return None
