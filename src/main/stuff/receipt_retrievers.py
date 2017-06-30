import time
from datetime import datetime, timedelta
from http import HTTPStatus
from logging import getLogger

import requests
from django.conf import settings
from lxml import etree


logger = getLogger(__name__)


class ReceiptRetriever:

    def get_receipt(self, **kwargs):
        raise NotImplementedError()


class _DefaultReceiptRetriever(ReceiptRetriever):

    MAX_TRIES = 5
    RETRY_DELAY = timedelta(seconds=5)

    def get_receipt(self, **kwargs):
        params = kwargs.get("fiscal_drive_number"), kwargs.get("fiscal_document_number"), kwargs.get("fiscal_sign")
        if not all(params):
            raise _NotEnoughParameters()
        return self._get_receipt(*params, try_number=1)

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
        receipt = response.json()['document']['receipt']
        return {
            'fiscal_drive_number': receipt['fiscalDriveNumber'],
            'fiscal_document_number': receipt['fiscalDocumentNumber'],
            'fiscal_sign': receipt['fiscalSign'],
            'seller_name': receipt['user'],
            'seller_individual_number': receipt['userInn'],
            'created': datetime.strptime(receipt['dateTime'], '%Y-%m-%dT%H:%M:%S') - timedelta(hours=4),
            'items': tuple({
                'barcode': item.get('barcode'),
                'name': item['name'],
                'price': str(item['price'] / 100),
                'quantity': str(item['quantity']),
                'total': str(item['sum'] / 100)
            } for item in receipt['items'])
        }


class _PlatformaOfdOperatorReceiptRetriever(ReceiptRetriever):

    def get_receipt(self, **kwargs):
        params = kwargs.get("fiscal_drive_number"), kwargs.get("fiscal_sign")
        if not all(params):
            raise _NotEnoughParameters()
        response = requests.get("https://lk.platformaofd.ru/web/noauth/cheque?fn=%s&fp=%s" % params)
        if response.status_code != HTTPStatus.OK:
            raise Exception("server response was %s (%s)" % (response.status_code, response.content))
        return self._parse_html(response.content)

    def _parse_html(self, html):
        tree = etree.XML(html, etree.HTMLParser())
        if not tree.xpath("//span[contains(@class, 'glyphicon-download-alt')]"):
            return None
        return {
            'fiscal_drive_number': self._get_second_column_text(tree, "заводской номер фискального накопителя", True),
            'fiscal_document_number': self._get_second_column_text(tree, "порядковый номер фискального документа", True),
            'fiscal_sign': self._get_second_column_text(tree, "фискальный признак документа", True),
            'seller_name': self._get_second_column_text(tree, "наименование пользователя"),
            'seller_individual_number': self._get_second_column_text(tree, "ИНН пользователя", True),
            'created': self._get_created(tree),
            'items': tuple(self._get_items(tree))
        }

    def _get_created(self, tree):
        return datetime.strptime(self._get_second_column_text(tree, "дата, время", True), '%d.%m.%Y %H:%M') - timedelta(hours=7)

    def _get_items(self, tree):
        strings = tree.xpath("//p[text()='наименование товара (реквизиты)']/ancestor::div[@class='row'][1]/following-sibling::div[position() >= 1 and position() <= 5]/div[contains(@class, 'text-right')]/p/text()")
        for i in range(0, len(strings), 5):
            yield {
                'name': strings[i],
                'barcode': strings[i + 1],
                'price': strings[i + 2],
                'quantity': strings[i + 3],
                'total': strings[i + 4]
            }

    def _get_second_column_text(self, tree, first_column_text, is_bold=False):
        return tree.xpath("//p[text()='%s']/ancestor::div[@class='row'][1]//div[contains(@class, 'text-right')]/p%s" % (first_column_text, '/b' if is_bold else ''))[0].text


class _TaxcomOperatorReceiptRetriever(ReceiptRetriever):

    def get_receipt(self, **kwargs):
        params = kwargs.get("fiscal_sign"), kwargs.get("total_sum")
        if not all(params):
            raise _NotEnoughParameters()
        response = requests.get("http://receipt.taxcom.ru/v01/show?fp=%s&s=%s" % params)
        if response.status_code != HTTPStatus.OK:
            raise Exception("server response was %s (%s)" % (response.status_code, response.content))
        return self._parse_html(response.content)

    def _parse_html(self, html):
        tree = etree.XML(html, etree.HTMLParser())
        if not tree.xpath("//h1[@id='receipt_title']"):
            return None
        return {
            'fiscal_drive_number': self._get_second_column_text(tree, "Зав.№ ФН"),
            'fiscal_document_number': self._get_second_column_text(tree, "№ ФД"),
            'fiscal_sign': self._get_second_column_text(tree, "ФПД"),
            'seller_name': self._get_seller_name(tree),
            'seller_individual_number': self._get_seller_individual_name(tree),
            'created': self._get_created(tree),
            'items': tuple(self._get_items(tree))
        }

    def _get_seller_name(self, tree):
        return tree.xpath("(//div[@class='receipt_report']//span)[1]")[0].text.strip()

    def _get_seller_individual_name(self, tree):
        return tree.xpath("(//div[@class='receipt_report']//span)[2]")[0].text.strip()

    def _get_created(self, tree):
        return datetime.strptime(tree.xpath("//span[text()='Приход']/parent::td/following-sibling::td[1]//span[2]")[0].text, '%d.%m.%Y %H:%M') - timedelta(hours=7)

    def _get_items(self, tree):
        strings = tree.xpath("//table[@class='verticalBlock']//span/text()")
        for i in range(0, len(strings) - 6, 9):
            yield {
                'name': strings[i],
                'quantity': strings[i + 1][:-4] if strings[i + 1].endswith(",000") else strings[i + 1].replace(",", "."),
                'price': strings[i + 2],
                'total': strings[i + 3]
            }

    def _get_second_column_text(self, tree, first_column_text):
        return tree.xpath("//td[text()='%s']/following-sibling::td[1]/span" % first_column_text)[0].text.strip()


class _OperatorReceiptRetriever(ReceiptRetriever):

    _retrievers = (
        _PlatformaOfdOperatorReceiptRetriever(),
        _TaxcomOperatorReceiptRetriever(),
    )

    def get_receipt(self, **kwargs):
        for retriever in self._retrievers:
            try:
                data = retriever.get_receipt(**kwargs)
                if data:
                    logger.debug("Receipt found via %s", retriever)
                    return data
            except _NotEnoughParameters:
                pass
        raise _OperatorNotSupportedException()


class _NotEnoughParameters(Exception):
    pass


class _OperatorNotSupportedException(Exception):
    pass


class _FallbackReceiptRetriever(ReceiptRetriever):

    _default_retriever = _DefaultReceiptRetriever()
    _operator_retriever = _OperatorReceiptRetriever()

    def get_receipt(self, **kwargs):
        try:
            return self._operator_retriever.get_receipt(**kwargs)
        except _OperatorNotSupportedException:
            return self._default_retriever.get_receipt(**kwargs)


def get_receipt_retriever():
    return _FallbackReceiptRetriever()
