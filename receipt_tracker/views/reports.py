from logging import getLogger
from typing import Dict, Tuple

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from receipt_tracker.models import *
from receipt_tracker.repositories import receipt_item_repository, receipt_repository
from receipt_tracker.views import add_common_context

logger = getLogger(__name__)

TOP_SIZE = 10


@login_required
def value_report_view(request):
    receipts = receipt_repository.get_last_by_buyer_id(request.user.id)

    context = {
        'receipts': list(map(_get_receipt_info, receipts)),
        'food': {
            'protein': sum(receipt.protein for receipt in receipts if receipt.protein is not None),
            'fat': sum(receipt.fat for receipt in receipts if receipt.fat is not None),
            'carbohydrate': sum(receipt.carbohydrate for receipt in receipts if receipt.carbohydrate is not None),
            'calories': sum(receipt.calories for receipt in receipts if receipt.calories is not None) / 1000,
        },
        'food_should_be': _get_food_should_be(receipts),
        'non_checked_count': sum(receipt.non_checked_product_count for receipt in receipts)
    }
    context = add_common_context(context)

    return render(request, 'reports/value.html', context)


def _get_receipt_info(receipt: Receipt) -> Dict:
    return {
        'id': receipt.id,
        'seller_name': receipt.seller.name,
        'created': receipt.created,
        'items': [{
            'product_id': item.product_alias.product.id,
            'name': item.product_alias.product.name,
            'price': item.price,
            'quantity': item.quantity,
            'total': item.total,
            'is_product_checked': item.is_product_checked
        } for item in receipt.items],
        'food': {
            'protein': receipt.protein,
            'fat': receipt.fat,
            'carbohydrate': receipt.carbohydrate,
            'calories': receipt.calories / 1000 if receipt.calories is not None else None
        },
        'non_checked_count': receipt.non_checked_product_count
    }


def _get_food_should_be(receipts: List[Receipt]) -> Dict:
    part = sum(receipt.protein + receipt.fat + receipt.carbohydrate for receipt in receipts
               if all((receipt.protein, receipt.fat, receipt.carbohydrate))) / 6
    return {
        'protein': part,
        'fat': part,
        'carbohydrate': part * 4,
    }


@login_required
def top_report_view(request):
    items = receipt_item_repository.get_last_by_buyer_id(request.user.id)

    context = {key: _get_top(func(items)) for key, func in (
        ('top_by_calories', _get_top_by_calories),
        ('top_by_total', _get_top_by_total),
        ('top_by_weight', _get_top_by_weight),
        ('top_by_protein', _get_top_by_protein),
        ('top_by_fat', _get_top_by_fat),
        ('top_by_carbohydrate', _get_top_by_carbohydrate),
        ('top_by_effectivity', _get_top_by_effectivity),
    )}
    context = add_common_context(context)

    return render(request, 'reports/top.html', context)


ProductStats = Tuple[Product, Decimal]


def _get_top(products: List[ProductStats]) -> List[Dict]:
    return [{
        'id': product.id,
        'name': product.name,
        'is_checked': product.is_checked,
        'value': value,
    } for product, value in products]


def _get_top_by_calories(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if not product.is_food:
            continue
        if product not in products:
            products[product] = 0
        products[product] += item.calories / 1000
    return sorted(products.items(), key=lambda item: item[1], reverse=True)[:TOP_SIZE]


def _get_top_by_total(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if product not in products:
            products[product] = 0
        products[product] += item.total
    return sorted(products.items(), key=lambda item: item[1], reverse=True)[:TOP_SIZE]


def _get_top_by_weight(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if not product.is_food:
            continue
        if product not in products:
            products[product] = 0
        products[product] += item.quantity * product.foodproduct.weight / 1000
    return sorted(products.items(), key=lambda item: item[1], reverse=True)[:TOP_SIZE]


def _get_top_by_protein(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if not product.is_food:
            continue
        if product not in products:
            products[product] = 0
        products[product] += item.protein / 1000
    return sorted(products.items(), key=lambda item: item[1], reverse=True)[:TOP_SIZE]


def _get_top_by_fat(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if not product.is_food:
            continue
        if product not in products:
            products[product] = 0
        products[product] += item.fat / 1000
    return sorted(products.items(), key=lambda item: item[1], reverse=True)[:TOP_SIZE]


def _get_top_by_carbohydrate(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if not product.is_food:
            continue
        if product not in products:
            products[product] = 0
        products[product] += item.carbohydrate / 1000
    return sorted(products.items(), key=lambda item: item[1], reverse=True)[:TOP_SIZE]


def _get_top_by_effectivity(items: List[ReceiptItem]) -> List[ProductStats]:
    products = {}
    for item in items:
        product = item.product_alias.product
        if not product.is_food:
            continue
        if product not in products:
            products[product] = []
        products[product].append(item.calories / float(item.total))
    products = ((product, sum(values) / len(values) / 1000) for product, values in products.items())
    return sorted(products, key=lambda item: item[1], reverse=True)[:TOP_SIZE]


class _FoodStats:

    def __init__(self):
        self.protein = 0
        self.fat = 0
        self.carbohydrate = 0
        self.calories = 0
        self.total = 0

    def add(self, item):
        self.protein += item.protein
        self.fat += item.fat
        self.carbohydrate += item.carbohydrate
        self.calories += item.calories / 1000
        self.total += item.total


class _NonFoodStats:

    def __init__(self):
        self.protein = None
        self.fat = None
        self.carbohydrate = None
        self.calories = None
        self.total = 0

    def add(self, item):
        self.total += item.total


COLUMNS = (
    ('protein', 'Белки'),
    ('fat', 'Жиры'),
    ('carbohydrate', 'Углеводы'),
    ('calories', 'Калорийность'),
    ('total', 'Стоимость'),
)


@login_required
def summary_report_view(request):
    items = receipt_item_repository.get_last_by_buyer_id(request.user.id)
    products = _get_summary(items)
    sorting_key = request.GET.get('sort')
    if sorting_key in (item[0] for item in COLUMNS):
        products = sorted(products, key=lambda pair: getattr(pair[1], sorting_key) or 0, reverse=True)

    context = {
        'columns': COLUMNS,
        'sorting_key': sorting_key,
        'products': [{
            'id': product.id,
            'name': product.name,
            'is_food': product.is_food,
            'is_checked': product.is_checked,
            'protein': stats.protein,
            'fat': stats.fat,
            'carbohydrate': stats.carbohydrate,
            'calories': stats.calories,
            'total': stats.total
        } for product, stats in products]
    }
    context = add_common_context(context)

    return render(request, 'reports/summary.html', context)


def _get_summary(items: List[ReceiptItem]) -> List[Tuple[Product, Union[_FoodStats, _NonFoodStats]]]:
    products: Dict[Product, Union[_FoodStats, _NonFoodStats]] = {}
    for item in items:
        product = item.product_alias.product
        stats = products.get(product)
        if stats is None:
            stats = _FoodStats() if product.is_food else _NonFoodStats()
            products[product] = stats
        stats.add(item)
    return list(products.items())
