from datetime import datetime, timedelta
from decimal import Decimal
from logging import getLogger
from typing import Dict, Union

from django.db.transaction import atomic

from receipt_tracker.celery import app
from receipt_tracker.lib import ReceiptParams
from receipt_tracker.lib.retrievers import ParsedReceipt, get_receipt_retriever
from receipt_tracker.repositories import product_alias_repository, product_repository, receipt_item_repository, \
    receipt_repository, seller_repository

logger = getLogger(__name__)

ReceiptParamsDict = Dict[str, Union[str, int]]


def receipt_params_to_dict(params: ReceiptParams) -> ReceiptParamsDict:
    return {
        'fiscal_drive_number': params.fiscal_drive_number,
        'fiscal_document_number': params.fiscal_document_number,
        'fiscal_sign': params.fiscal_sign,
        'created': params.created.isoformat(),
        'amount': str(params.amount),
    }


def dict_to_receipt_params(params: ReceiptParamsDict) -> ReceiptParams:
    return ReceiptParams(
        params['fiscal_drive_number'],
        params['fiscal_document_number'],
        params['fiscal_sign'],
        datetime.fromisoformat(params['created']),
        Decimal(params['amount']),
    )


@app.task(bind=True)
def add_receipt(task, user_id: int, raw_params: ReceiptParamsDict):
    params = dict_to_receipt_params(raw_params)
    if receipt_repository.is_exist(params.fiscal_drive_number, params.fiscal_document_number, params.fiscal_sign):
        logger.info('Receipt %s already exists', params)
        return

    logger.info('Adding receipt by params %s for user %s', params, user_id)
    if not _retrieve_receipt(user_id, params):
        logger.info('Receipt not retrieved, rescheduling task')
        task.retry(countdown=timedelta(hours=1).total_seconds())


def _retrieve_receipt(user_id: int, params: ReceiptParams) -> bool:
    try:
        parsed_receipt = get_receipt_retriever().get_receipt(params)
        if not parsed_receipt:
            logger.info('Retriever returned no receipt')
            return False
        logger.info('Receipt retrieved, storing to database')
        _store_to_db(user_id, parsed_receipt)
        return True
    except Exception as e:
        logger.warning('Cannot retrieve receipt: %s', e)
    return False


@atomic
def _store_to_db(user_id: int, parsed_receipt: ParsedReceipt):
    seller = seller_repository.get_or_create(parsed_receipt.seller_individual_number, parsed_receipt.seller_name)
    receipt = receipt_repository.create(seller.id, user_id, parsed_receipt.created, parsed_receipt.fiscal_drive_number,
                                        parsed_receipt.fiscal_document_number, parsed_receipt.fiscal_sign)

    for parsed_receipt_item in parsed_receipt.items:
        product_alias = product_alias_repository.get_by_seller_and_name(seller.id, parsed_receipt_item.name)
        if not product_alias:
            logger.debug('No product alias found, creating new one')
            product = product_repository.create()
            product_alias = product_alias_repository.create(seller.id, product.id, parsed_receipt_item.name)
            logger.info('Product %s and product alias %s created', product, product_alias)

        receipt_item = receipt_item_repository.create(receipt.id, product_alias.id, parsed_receipt_item.price,
                                                      parsed_receipt_item.quantity, parsed_receipt_item.total)
        logger.debug('Receipt item %s created', receipt_item)

    logger.info('Receipt %s created', receipt)
