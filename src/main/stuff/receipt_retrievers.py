import time
from datetime import datetime, timedelta
from http import HTTPStatus
from logging import getLogger

import requests
from django.conf import settings
from lxml import etree


logger = getLogger(__name__)


class ReceiptRetriever:

    def get_receipt(self, fiscal_drive_number, fiscal_document_number, fiscal_sign):
        raise NotImplementedError()


class _DefaultReceiptRetriever(ReceiptRetriever):

    MAX_TRIES = 5
    RETRY_DELAY = timedelta(seconds=5)

    def get_receipt(self, fiscal_drive_number, fiscal_document_number, fiscal_sign):
        return self._get_receipt(fiscal_drive_number, fiscal_document_number, fiscal_sign, 1)

    def _get_receipt(self, fiscal_drive_number, fiscal_document_number, fiscal_sign, try_number):
        logger.debug("Retrieving receipt JSON")
        response = requests.get(
            "http://proverkacheka.nalog.ru:8888/v1/inns/*/kkts/*/fss/%s/tickets/%s?fiscalSign=%s&sendToEmail=no" % (fiscal_drive_number, fiscal_document_number, fiscal_sign),
            auth=(settings.CHECKER_LOGIN, settings.CHECKER_PASSWORD),
            headers={
                "Device-Id": settings.CHECKER_DEVICE_ID,
                "Device-OS": settings.CHECKER_DEVICE_OS,
            })
        if response.status_code == HTTPStatus.ACCEPTED:
            if try_number == self.MAX_TRIES:
                raise Exception("no result after %s tries" % try_number)
            else:
                logger.debug("Server response was %s, retrying in several seconds", response.status_code)
                time.sleep(self.RETRY_DELAY.total_seconds())
                return self._get_receipt(fiscal_drive_number, fiscal_document_number, fiscal_sign, try_number + 1)
        if response.status_code != HTTPStatus.OK:
            raise Exception("server response was %s (%s)" % (response.status_code, response.content.decode("utf-8")))
        return response.json()


class _PlatformaOfdOperatorReceiptRetriever:

    def get_receipt(self, fiscal_drive_number, fiscal_document_number, fiscal_sign):
        response = requests.get("https://lk.platformaofd.ru/web/noauth/cheque?fn=%s&fp=%s" % (fiscal_drive_number, fiscal_sign))
        if response.status_code != HTTPStatus.OK:
            raise Exception("server response was %s (%s)" % (response.status_code, response.content))
        return self._parse_html(response.content)

    def _parse_html(self, html):
        tree = etree.XML(html, etree.HTMLParser())
        if not tree.xpath("//span[contains(@class, 'glyphicon-download-alt')]"):
            return None
        return {
            'document': {
                'receipt': {
                    'fiscalDriveNumber': self._get_second_column_text(tree, "заводской номер фискального накопителя", True),
                    'fiscalDocumentNumber': self._get_second_column_text(tree, "порядковый номер фискального документа", True),
                    'fiscalSign': self._get_second_column_text(tree, "фискальный признак документа", True),
                    'user': self._get_second_column_text(tree, "наименование пользователя"),
                    'userInn': self._get_second_column_text(tree, "ИНН пользователя", True),
                    'dateTime': datetime.strptime(self._get_second_column_text(tree, "дата, время", True), '%d.%m.%Y %H:%M').strftime('%Y-%m-%dT%H:%M:%S'),
                    'items': tuple(self._get_items(tree))
                }
            }
        }

    def _get_items(self, tree):
        strings = tree.xpath("//p[text()='наименование товара (реквизиты)']/ancestor::div[@class='row'][1]/following-sibling::div[position() >= 1 and position() <= 5]/div[contains(@class, 'text-right')]/p/text()")
        for i in range(0, len(strings), 5):
            yield {
                'name': strings[i],
                'barcode': strings[i + 1],
                'price': strings[i + 2],
                'quantity': strings[i + 3],
                'sum': strings[i + 4]
            }

    def _get_second_column_text(self, tree, first_column_text, is_bold=False):
        return tree.xpath("//p[text()='%s']/ancestor::div[@class='row'][1]//div[contains(@class, 'text-right')]/p%s" % (first_column_text, '/b' if is_bold else ''))[0].text


class _OperatorReceiptRetriever(ReceiptRetriever):

    _retrievers = (
        _PlatformaOfdOperatorReceiptRetriever(),
    )

    def get_receipt(self, *args):
        for retriever in self._retrievers:
            data = retriever.get_receipt(*args)
            if data:
                logger.debug("Receipt found via %s", retriever)
                return data
        raise _OperatorNotSupportedException()


class _OperatorNotSupportedException(Exception):
    pass


class _FallbackReceiptRetriever(ReceiptRetriever):

    _default_retriever = _DefaultReceiptRetriever()
    _operator_retriever = _OperatorReceiptRetriever()

    def get_receipt(self, *args):
        try:
            return self._operator_retriever.get_receipt(*args)
        except _OperatorNotSupportedException:
            return self._default_retriever.get_receipt(*args)


def get_receipt_retriever():
    return _FallbackReceiptRetriever()
