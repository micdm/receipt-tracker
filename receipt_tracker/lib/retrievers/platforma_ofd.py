from datetime import datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from logging import getLogger
from typing import List, Optional

import requests
from lxml import etree

from receipt_tracker.lib import ReceiptParams
from receipt_tracker.lib.retrievers import BadResponse, ParsedReceipt, ParsedReceiptItem, ReceiptRetriever

logger = getLogger(__name__)


class PlatformaOfdOperatorReceiptRetriever(ReceiptRetriever):

    def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
        url = f'https://lk.platformaofd.ru/web/noauth/cheque?fn={params.fiscal_drive_number}&fp={params.fiscal_sign}'
        logger.debug('Downloading receipt from %s', url)
        response = requests.get(url)
        if response.status_code != HTTPStatus.OK:
            raise BadResponse(f'server response was {response.status_code} ({response.content})')
        return Parser().parse(response.content)


class Parser:

    def parse(self, html: str) -> Optional[ParsedReceipt]:
        tree = etree.XML(html, etree.HTMLParser())
        if not tree.xpath('//i[contains(@class, "ofdicon-download")]'):
            return None
        return ParsedReceipt(
            self._get_second_column_text(tree, 'N ФН'),
            self._get_second_column_text(tree, 'N ФД'),
            self._get_second_column_text(tree, 'ФП'),
            tree.xpath('//div[@class="check-top"]/div')[0].text,
            tree.xpath('//div[@class="check-top"]/div')[2].text[4:],
            self._get_created(tree),
            list(self._get_items(tree) if self._has_barcodes(tree) else self._get_items_with_no_barcodes(tree)),
        )

    def _get_created(self, tree) -> datetime:
        return datetime.strptime(self._get_second_column_text(tree, 'Приход'), '%d.%m.%Y %H:%M')

    def _has_barcodes(self, tree) -> bool:
        return tree.xpath('//div[text()="штриховой код EAN13"]')

    def _get_items(self, tree) -> List[ParsedReceiptItem]:
        strings = tree.xpath('''
            //div[@class='check-product-name']
            /ancestor::div[@class='check-section']
            //div[contains(@class, 'check-product-name') or contains(@class, 'check-col')]
            /text()
        ''')
        for i in range(0, len(strings), 8):
            yield ParsedReceiptItem(
                strings[i].strip(),
                strings[i + 1].split(' х ')[0],
                strings[i + 1].split(' х ')[1],
                strings[i + 7],
            )

    def _get_items_with_no_barcodes(self, tree) -> List[ParsedReceiptItem]:
        sections = tree.xpath('''
            //div[@class='check-product-name']
            /ancestor::div[@class='check-section']
        ''')
        for section in sections:
            name = section.xpath('.//div[@class="check-product-name"]')[0].text.strip()
            nodes = section.xpath('.//div[contains(@class, "check-col-right")]')
            quantity, price = nodes[0].text.split(' х ')
            total = nodes[-1].text
            yield ParsedReceiptItem(name, Decimal(quantity), Decimal(price), Decimal(total))

    def _get_second_column_text(self, tree, first_column_text: str) -> str:
        return tree.xpath(f'''
            //div[text()="{first_column_text}"]
            /ancestor::div[@class="check-row"][1]
            /div[contains(@class, "check-col-right")]
        ''')[0].text
