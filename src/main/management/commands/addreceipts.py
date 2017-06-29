import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from http import HTTPStatus
from logging import getLogger

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction

from main.models import AddReceiptTask, Seller, Receipt, Product, ProductAlias, ReceiptItem
from main.stuff.receipt_retrievers import get_receipt_retriever

logger = getLogger(__name__)


class Command(BaseCommand):

    _receipt_retriever = get_receipt_retriever()

    def handle(self, *args, **options):
        logger.info("Checking for unhandled receipts")
        tasks = AddReceiptTask.objects.filter(created__gt=datetime.utcnow() - timedelta(days=7),
                                              status__in=(AddReceiptTask.STATUS_NEW, AddReceiptTask.STATUS_INCOMPLETE))
        logger.info("%s tasks found", len(tasks))
        for task in tasks:
            self._handle_task(task)

    def _handle_task(self, task):
        logger.info("Handling task %s", task)
        try:
            with transaction.atomic():
                self._set_task_status(task.id, AddReceiptTask.STATUS_INCOMPLETE)
                data = self._receipt_retriever.get_receipt(task.fiscal_drive_number, task.fiscal_document_number, task.fiscal_sign)
                logger.debug('Receipt JSON is %s', data)
                receipt = self._save_receipt(data['document']['receipt'], task.buyer)
                self._set_task_status(task.id, AddReceiptTask.STATUS_COMPLETE)
                logger.info("Task complete, receipt ID is %s", receipt.id)
        except Exception as e:
            logger.info("Cannot complete task: %s", e)

    def _save_receipt(self, data, user):
        logger.debug("Storing receipt into database")
        seller = Seller.objects.get_or_create(individual_number=data['userInn'], defaults={'name': data['user']})[0]
        receipt = Receipt.objects.create(seller=seller, buyer=user,
                                         created=datetime.strptime(data['dateTime'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone(timedelta(hours=4))).astimezone(timezone.utc),
                                         fiscal_drive_number=data['fiscalDriveNumber'],
                                         fiscal_document_number=data['fiscalDocumentNumber'],
                                         fiscal_sign=data['fiscalSign'])
        for item in data['items']:
            if 'barcode' in item:
                product = Product.objects.get_or_create(barcode=item['barcode'])[0]
                product_alias = ProductAlias.objects.get_or_create(seller=seller, product=product, name=item['name'])[0]
            else:
                product_alias = ProductAlias.objects.filter(seller=seller, name=item['name']).first()
                if not product_alias:
                    product = Product.objects.create()
                    product_alias = ProductAlias.objects.create(seller=seller, product=product, name=item['name'])
            ReceiptItem.objects.create(receipt=receipt, product_alias=product_alias,
                                       price=Decimal(item['price'] / 100),
                                       quantity=Decimal(item['quantity']),
                                       total=Decimal(item['sum'] / 100))
        return receipt

    def _set_task_status(self, task_id, status):
        AddReceiptTask.objects.filter(id=task_id).update(status=status)
