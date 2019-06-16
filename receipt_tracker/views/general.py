from logging import getLogger

from django.contrib.auth.decorators import login_required
from django.db.transaction import atomic
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, reverse
from django.views.decorators.csrf import csrf_exempt

from receipt_tracker import forms, tasks
from receipt_tracker.lib import qr_code
from receipt_tracker.lib.similar import SimilarProductFinder
from receipt_tracker.repositories import product_repository, receipt_item_repository, receipt_repository
from receipt_tracker.tasks import receipt_params_to_dict
from receipt_tracker.views import add_common_context

logger = getLogger(__name__)


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
    context = add_common_context(context)
    return render(request, 'index.html', context)


@login_required
@csrf_exempt
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
                tasks.add_receipt.apply(args=(request.user.id, receipt_params_to_dict(params)))
                return HttpResponseRedirect(reverse('receipt-added'))
    else:
        form = forms.QrForm()

    context = {
        'form': form,
    }
    context = add_common_context(context)
    return render(request, 'add_receipt.html', context)


def receipt_added_view(request):
    context = {}
    context = add_common_context(context)
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
    context = add_common_context(context)
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

    details = product.details
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
                'calories': details.calories / 1000,
                'protein': details.protein,
                'fat': details.fat,
                'carbohydrate': details.carbohydrate,
                'weight': details.weight / 1000,
                'total': {
                    'calories': details.total_calories / 1000,
                    'protein': details.total_protein,
                    'fat': details.total_fat,
                    'carbohydrate': details.total_carbohydrate
                }
            } if product.is_food else None,
            'similars': [{
                'id': similar.product.id,
                'name': similar.product.name,
                'confidence': similar.confidence,
            } for similar in SimilarProductFinder(list(product_repository.get_all())).find(product.name)]
        },
        'edit': {
            'is_allowed': is_edit_allowed,
            'barcode_form': barcode_form
        }
    }
    context = add_common_context(context)

    return render(request, 'product.html', context)
