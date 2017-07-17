import decimal
import re
import subprocess
import time
from datetime import datetime, timezone, timedelta
from http import HTTPStatus
from logging import getLogger

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, reverse
from django.utils.decorators import method_decorator
from django.views import View

from main import forms
from main.models import *

logger = getLogger(__name__)


def _get_context(context=None):
    if not context:
        context = {}
    context.update({
        'google_analytics_id': settings.GOOGLE_ANALYTICS_ID if not settings.DEBUG else None
    })
    return context


class IndexView(View):

    def get(self, request):
        receipt_items = ReceiptItem.objects.order_by('-receipt__created')[:50]
        return render(request, 'index.html', _get_context(self._get_context(receipt_items)))

    def _get_context(self, receipt_items):
        return {
            'items': [{
                'product_id': item.product_alias.product.id,
                'is_product_checked': item.is_product_checked,
                'name': item.product_alias.name,
                'seller': item.receipt.seller.name,
                'price': item.price
            } for item in receipt_items]
        }


class AddReceiptView(View):

    @method_decorator(login_required)
    def get(self, request):
        return render(request, 'add_receipt.html', _get_context({
            'qr_form': forms.QrForm(),
            'manual_input_form': forms.ManualInputForm(),
            'photo_form': forms.PhotoForm()
        }))

    @method_decorator(login_required)
    def post(self, request):
        if 'qr' in request.POST:
            qr_form = forms.QrForm(request.POST)
            if qr_form.is_valid():
                try:
                    params = self._get_receipt_params_from_qr(qr_form.cleaned_data['text'])
                    self._add_receipt_task(request.user, *params)
                    return HttpResponseRedirect(reverse('receipt_added'))
                except Exception as e:
                    logger.debug('Cannot add receipt: %s', e)
                    qr_form.add_error(None, 'Не удалось добавить чек: %s' % e)
        else:
            qr_form = forms.QrForm()
        if 'manual' in request.POST:
            manual_input_form = forms.ManualInputForm(request.POST)
            if manual_input_form.is_valid():
                try:
                    self._add_receipt_task(request.user, manual_input_form.cleaned_data['fiscal_drive_number'],
                                           manual_input_form.cleaned_data['fiscal_document_number'],
                                           manual_input_form.cleaned_data['fiscal_sign'],
                                           manual_input_form.cleaned_data['total_sum'])
                    return HttpResponseRedirect(reverse('receipt_added'))
                except Exception as e:
                    logger.debug('Cannot add receipt: %s', e)
                    manual_input_form.add_error(None, 'Не удалось добавить чек: %s' % e)
        else:
            manual_input_form = forms.ManualInputForm()
        if 'photo' in request.POST:
            photo_form = forms.PhotoForm(request.POST, request.FILES)
            if photo_form.is_valid():
                try:
                    params = self._get_receipt_params_from_photo(photo_form.cleaned_data['photo'])
                    self._add_receipt_task(request.user, *params)
                    return HttpResponseRedirect(reverse('receipt_added'))
                except Exception as e:
                    logger.debug('Cannot add receipt: %s', e)
                    photo_form.add_error(None, 'Не удалось добавить чек: %s' % e)
        else:
            photo_form = forms.PhotoForm()
        return render(request, 'add_receipt.html', _get_context({
            'qr_form': qr_form,
            'manual_input_form': manual_input_form,
            'photo_form': photo_form
        }))

    def _get_receipt_params_from_qr(self, text):
        try:
            return tuple(re.search(pattern, text).group(1) for pattern in (r'fn=(\d+)', r'i=(\d+)', r'fp=(\d+)', r's=([\d.]+)'))
        except Exception:
            raise Exception('не удалось разобрать QR-текст')

    def _get_receipt_params_from_photo(self, photo):
        try:
            output = subprocess.run(('zbarimg', '-q', '--raw', photo.temporary_file_path()), stdout=subprocess.PIPE,
                                    check=True).stdout.decode('utf-8')
            return self._get_receipt_params_from_qr(output)
        except Exception as e:
            raise Exception('не удалось распознать QR-код на фотографии: %s' % e)

    def _add_receipt_task(self, user, fiscal_drive_number, fiscal_document_number, fiscal_sign, total_sum):
        with transaction.atomic():
            if AddReceiptTask.objects.filter(fiscal_drive_number=fiscal_drive_number,
                                             fiscal_document_number=fiscal_document_number,
                                             fiscal_sign=fiscal_sign).exists():
                raise Exception('чек уже добавлен')
            AddReceiptTask.objects.create(fiscal_drive_number=fiscal_drive_number,
                                          fiscal_document_number=fiscal_document_number,
                                          fiscal_sign=fiscal_sign,
                                          total_sum=total_sum,
                                          buyer=user)


class ReceiptAddedView(View):

    def get(self, request):
        return render(request, 'receipt_added.html', _get_context())


class ProductView(View):

    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)
        if not product:
            return HttpResponseNotFound()
        return render(request, 'product.html', _get_context(self._get_context(product, product.foodproduct if hasattr(product, 'foodproduct') else None)))

    def _get_context(self, product, food_product):
        return {
            'product': {
                'id': product.id,
                'name': product.name,
                'is_food': product.is_food,
                'is_non_food': product.is_non_food,
                'aliases': tuple({
                    'id': alias.id,
                    'seller': alias.seller.name,
                    'name': alias.name,
                } for alias in product.productalias_set.all()),
                'prices': tuple({
                    'seller': item.receipt.seller.name,
                    'created': item.receipt.created,
                    'value': item.price,
                } for item in ReceiptItem.objects.filter(product_alias__product=product).order_by('-receipt__created')),
                'food': {
                    'calories': food_product.calories / 1000,
                    'protein': food_product.protein,
                    'fat': food_product.fat,
                    'carbohydrate': food_product.carbohydrate,
                    'weight': food_product.weight
                } if food_product else None
            }
        }


class ValueReportView(View):

    @method_decorator(login_required)
    def get(self, request):
        receipts = Receipt.objects\
            .filter(buyer=request.user, created__range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()))\
            .order_by('-created')
        return render(request, 'reports/value.html', _get_context(self._get_context(receipts)))

    def _get_context(self, receipts):
        return {
            'receipts': tuple(map(self._get_receipt_info, receipts)),
            'food': {
                'protein': sum(receipt.protein for receipt in receipts),
                'fat': sum(receipt.fat for receipt in receipts),
                'carbohydrate': sum(receipt.carbohydrate for receipt in receipts),
                'calories': sum(receipt.calories for receipt in receipts) / 1000,
            },
            'non_checked_count': sum(receipt.non_checked_product_count for receipt in receipts)
        }

    def _get_receipt_info(self, receipt):
        items = receipt.receiptitem_set.all().order_by('product_alias__name')
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
            } for item in items],
            'food': {
                'protein': receipt.protein,
                'fat': receipt.fat,
                'carbohydrate': receipt.carbohydrate,
                'calories': receipt.calories / 1000
            },
            'non_checked_count': receipt.non_checked_product_count
        }


class TopReportView(View):

    @method_decorator(login_required)
    def get(self, request):
        most_consumed = self._get_most_consumed()
        return render(request, 'reports/top.html', _get_context(self._get_context(most_consumed)))

    def _get_most_consumed(self):
        products = {}
        for item in ReceiptItem.objects.filter(receipt__created__range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow())):
            product = item.product_alias.product
            if product not in products:
                products[product] = 0
            products[product] += item.quantity
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:10]

    def _get_context(self, most_consumed):
        return {
            'most_consumed': tuple({
                'name': product.name,
                'quantity': quantity,
                'weight': product.foodproduct.weight * quantity if product.is_food else None,
            } for product, quantity in most_consumed)
        }
