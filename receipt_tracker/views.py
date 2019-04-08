from logging import getLogger
from typing import Dict, Tuple

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.transaction import atomic
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, reverse

from receipt_tracker import forms
from receipt_tracker.lib import qr_code
from receipt_tracker.models import *
from receipt_tracker.repositories import product_repository, receipt_item_repository, receipt_repository
from receipt_tracker.tasks import add_receipt, receipt_params_to_dict

logger = getLogger(__name__)

TOP_SIZE = 10


def _add_common_context(context: Dict) -> Dict:
    context.update({
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID if not settings.DEBUG else None
    })
    return context


def index_view(request):
    receipt_items = receipt_item_repository.get_last()
    context = {
        'items': [{
            'product_id': item.product_alias.product.id,
            'is_product_checked': item.is_product_checked,
            'name': item.product_alias.name,
            'seller': item.receipt.seller.name,
            'price': item.price
        } for item in receipt_items]
    }
    context = _add_common_context(context)
    return render(request, 'index.html', context)


@login_required
def add_receipt_view(request):
    if request.method == 'POST':
        form = forms.QrForm(request.POST)
        if form.is_valid():
            params = qr_code.decode(form.cleaned_data['text'])
            if not params:
                form.add_error(None, 'Не удалось разобрать код')
            elif receipt_repository.is_exist(params.fiscal_drive_number, params.fiscal_document_number,
                                             params.fiscal_sign):
                form.add_error(None, 'Чек уже добавлен')
            else:
                add_receipt.apply(args=(request.user.id, receipt_params_to_dict(params)))
                return HttpResponseRedirect(reverse('receipt-added'))
    else:
        form = forms.QrForm()

    context = {
        'form': form,
    }
    context = _add_common_context(context)
    return render(request, 'add_receipt.html', context)


def receipt_added_view(request):
    context = {}
    context = _add_common_context(context)
    return render(request, 'receipt_added.html', context)


def products_view(request):
    products = product_repository.get_all()
    context = {
        'products': [{
            'id': product.id,
            'name': product.name,
            'is_checked': product.is_checked,
            'last_buy': product.last_buy,
            'last_price': product.last_price
        } for product in products]
    }
    context = _add_common_context(context)
    return render(request, 'products.html', context)


def product_view(request, product_id: int):
    product = product_repository.get_by_id(product_id)
    if not product:
        return HttpResponseNotFound()

    is_edit_allowed = receipt_item_repository.is_exist_by_product_id_and_buyer_id(product_id, request.user.id)

    if request.method == 'POST':
        if not is_edit_allowed:
            return HttpResponseForbidden()
        barcode_form = forms.BarcodeForm(request.POST)
        if barcode_form.is_valid():
            with atomic():
                original_product_id = product_repository.set_barcode(product_id, barcode_form.cleaned_data['barcode'])
            if original_product_id:
                return HttpResponseRedirect(reverse('product', args=(original_product_id,)))
            else:
                barcode_form.add_error(None, 'Штрихкод не найден')
    else:
        barcode_form = forms.BarcodeForm(initial={'barcode': product.barcode})

    food_product = product.details
    context = {
        'product': {
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'is_food': product.is_food,
            'is_non_food': product.is_non_food,
            'aliases': [{
                'id': alias.id,
                'seller': alias.seller.name,
                'name': alias.name,
            } for alias in product.aliases],
            'prices': [{
                'seller': item.receipt.seller.name,
                'created': item.receipt.created,
                'value': item.price,
            } for item in receipt_item_repository.get_by_product_id(product_id)],
            'food': {
                'calories': food_product.calories / 1000,
                'protein': food_product.protein,
                'fat': food_product.fat,
                'carbohydrate': food_product.carbohydrate,
                'weight': food_product.weight / 1000,
                'total': {
                    'calories': food_product.total_calories / 1000,
                    'protein': food_product.total_protein,
                    'fat': food_product.total_fat,
                    'carbohydrate': food_product.total_carbohydrate
                }
            } if food_product else None
        },
        'edit': {
            'is_allowed': is_edit_allowed,
            'barcode_form': barcode_form
        }
    }
    context = _add_common_context(context)

    return render(request, 'product.html', context)


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
    context = _add_common_context(context)

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
    context = _add_common_context(context)

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
    context = _add_common_context(context)

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
