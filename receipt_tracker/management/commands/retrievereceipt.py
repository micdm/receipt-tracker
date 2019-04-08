from logging import getLogger
from typing import Dict

from django.core.management import BaseCommand, CommandError

from receipt_tracker.lib.qr_code import decode
from receipt_tracker.lib.retrievers import ReceiptRetriever, get_available_receipt_retrievers

logger = getLogger(__name__)


class Command(BaseCommand):

    RECEIPT_RETRIEVERS: Dict[str, ReceiptRetriever] = {type(r).__name__: r for r in get_available_receipt_retrievers()}

    def add_arguments(self, parser):
        parser.add_argument('--retriever', choices=self.RECEIPT_RETRIEVERS.keys(), required=True)
        parser.add_argument('code')

    def handle(self, *args, **options):
        params = decode(options['code'])
        if not params:
            raise CommandError('cannot parse code')
        receipt_retriever = self.RECEIPT_RETRIEVERS.get(options['retriever'])
        parsed_receipt = receipt_retriever.get_receipt(params)
        if not parsed_receipt:
            raise CommandError('no receipt found')
        logger.info('Receipt successfully retrieved: %s', parsed_receipt)
