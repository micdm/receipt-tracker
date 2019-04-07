from datetime import datetime, timedelta
from decimal import Decimal
from http import HTTPStatus
from typing import List, Optional, Union

import requests
from lxml import etree

from receipt_tracker.lib import ReceiptParams
from receipt_tracker.lib.retrievers import BadResponse, ParsedReceipt, ParsedReceiptItem, ReceiptRetriever


class TaxcomOperatorReceiptRetriever(ReceiptRetriever):

    def get_receipt(self, params: ReceiptParams) -> Optional[ParsedReceipt]:
        response = requests.get(f'http://receipt.taxcom.ru/v01/show?fp={params.fiscal_sign}&s={params.amount}')
        if response.status_code != HTTPStatus.OK:
            raise BadResponse(f'server response was {response.status_code} ({response.content})')
        return Parser().parse(response.content)


class Parser:

    def parse(self, html) -> Optional[ParsedReceipt]:
        tree = etree.XML(html, etree.HTMLParser())
        if not tree.xpath('//h1[@id="receipt_title"]'):
            return None
        parser = self._get_parser(tree)
        return ParsedReceipt(
            parser.get_second_column_text(tree, 'Зав.№ ФН'),
            parser.get_second_column_text(tree, '№ ФД'),
            parser.get_second_column_text(tree, 'ФПД'),
            parser.get_seller_name(tree),
            parser.get_seller_individual_number(tree),
            parser.get_created(tree),
            list(parser.get_items(tree))
        )

    def _get_parser(self, tree) -> Union['ParserV1', 'ParserV2']:
        return ParserV1() if tree.xpath('//td[text()="№ смены"]') else ParserV2()


class ParserV1:

    def get_seller_name(self, tree) -> str:
        return tree.xpath('(//div[@class="receipt_report"]//span)[1]')[0].text.strip()

    def get_seller_individual_number(self, tree) -> str:
        return tree.xpath('(//div[@class="receipt_report"]//span)[2]')[0].text.strip()

    def get_created(self, tree) -> datetime:
        value = tree.xpath('//span[text()="Приход"]/parent::td/following-sibling::td[1]//span[2]')[0].text
        return datetime.strptime(value, '%d.%m.%Y %H:%M') - timedelta(hours=7)

    def get_items(self, tree) -> List[ParsedReceiptItem]:
        strings = tree.xpath('//table[@class="verticalBlock"]//span/text()')
        for i in range(0, len(strings) - 8, 9):
            yield ParsedReceiptItem(
                strings[i],
                Decimal(strings[i + 1][:-4] if strings[i + 1].endswith(',000') else strings[i + 1].replace(',', '.')),
                Decimal(strings[i + 2]),
                Decimal(strings[i + 3]),
            )

    def get_second_column_text(self, tree, first_column_text) -> str:
        return tree.xpath(f'//td[text()="{first_column_text}"]/following-sibling::td[1]/span')[0].text.strip()


class ParserV2:

    def get_seller_name(self, tree) -> str:
        return tree.xpath('(//div[@class="receipt_report"]//span)[1]')[0].text.strip()

    def get_seller_individual_number(self, tree) -> str:
        return tree.xpath('(//div[@class="receipt_report"]//span)[2]')[0].text.strip()

    def get_created(self, tree) -> datetime:
        value = tree.xpath('(//div[@class="receipt_report"]//span)[9]')[0].text.strip()
        return datetime.strptime(value,'%d.%m.%Y %H:%M') - timedelta(hours=7)

    def get_items(self, tree) -> List[ParsedReceiptItem]:
        strings = tree.xpath('//table[@class="verticalBlock"]//span/text()')
        for i in range(0, len(strings), 12):
            yield ParsedReceiptItem(
                strings[i],
                Decimal(strings[i + 1][:-4] if strings[i + 1].endswith('.000') else strings[i + 1]),
                Decimal(strings[i + 2]),
                Decimal(strings[i + 4]),
            )

    def get_second_column_text(self, tree, first_column_text) -> str:
        return tree.xpath(f'''
            //span[text()="{first_column_text}"]
            /parent::td
            /following-sibling::td[1]
            /span
        ''')[0].text.strip()
