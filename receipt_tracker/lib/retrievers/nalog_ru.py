import time
from datetime import datetime, timedelta
from http import HTTPStatus
from logging import getLogger
from typing import Optional

import requests
from django.conf import settings
from requests import Response

from receipt_tracker.lib import ReceiptParams
from receipt_tracker.lib.retrievers import BadResponse, ParsedReceipt, ParsedReceiptItem, ReceiptRetriever

logger = getLogger(__name__)


class NalogRuReceiptRetriever(ReceiptRetriever):

    MAX_TRIES = 5
    RETRY_DELAY = timedelta(seconds=5)

    def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
        self._check_if_receipt_exists(params)
        return self._get_receipt(params)

    def _make_request(self, url: str) -> Response:
        return requests.get(
            url,
            auth=(settings.CHECKER_LOGIN, settings.CHECKER_PASSWORD),
            headers={
                'Device-Id': settings.CHECKER_DEVICE_ID,
                'Device-OS': settings.CHECKER_DEVICE_OS,
            })

    def _check_if_receipt_exists(self, params: ReceiptParams):
        logger.debug('Checking if receipt exists')
        response = self._make_request(
            f'https://proverkacheka.nalog.ru:9999/v1/ofds/*/inns/*/fss/{params.fiscal_document_number}/operations'
            f'/1/tickets/{params.fiscal_drive_number}?fiscalSign={params.fiscal_sign}'
            f'&date={params.created.strftime("%Y-%m-%dT%H:%M:%S")}&sum={params.amount * 100}'
        )

        if response.status_code != HTTPStatus.NO_CONTENT:
            raise BadResponse(f'cannot check receipt, server response was {response.status_code} ({response.text})')

        logger.debug('It looks like receipt does exist')

    def _get_receipt(self, params: ReceiptParams, try_number: int = 1) -> Optional[ParsedReceipt]:
        logger.debug('Retrieving receipt JSON')
        response = self._make_request(
            f'https://proverkacheka.nalog.ru:9999/v1/inns/*/kkts/*/fss/{params.fiscal_drive_number}/tickets'
            f'/{params.fiscal_document_number}?fiscalSign={params.fiscal_sign}&sendToEmail=no',
        )

        if response.status_code == HTTPStatus.ACCEPTED:
            if try_number == self.MAX_TRIES:
                raise BadResponse(f'no result after {try_number} tries')
            else:
                logger.debug('Server response was %s, retrying in several seconds', response.status_code)
                time.sleep(self.RETRY_DELAY.total_seconds())
                return self._get_receipt(params, try_number + 1)

        if response.status_code != HTTPStatus.OK:
            raise BadResponse(f'cannot get receipt, server response was {response.status_code} ({response.text})')

        receipt = response.json()['document']['receipt']
        return ParsedReceipt(
            receipt['fiscalDriveNumber'],
            str(receipt['fiscalDocumentNumber']),
            str(receipt['fiscalSign']),
            receipt['user'],
            receipt['userInn'],
            datetime.strptime(receipt['dateTime'], '%Y-%m-%dT%H:%M:%S'),
            [ParsedReceiptItem(
                item['name'],
                str(item['quantity']),
                str(round(item['price'] / 100, 2)),
                str(round(item['sum'] / 100, 2)),
            ) for item in receipt['items']]
        )
