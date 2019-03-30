import re
import subprocess
from datetime import datetime, timedelta
from logging import getLogger

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, reverse
from django.utils.decorators import method_decorator
from django.views import View

from receipt_tracker import forms
from receipt_tracker.models import *

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


class ProductsView(View):

    def get(self, request):
        products = sorted(Product.objects.all(), key=lambda product: product.last_buy, reverse=True)
        return render(request, 'products.html', _get_context(self._get_context(products)))

    def _get_context(self, products):
        return {
            'products': tuple({
                'id': product.id,
                'name': product.name,
                'is_checked': product.is_checked,
                'last_buy': product.last_buy,
                'last_price': product.last_price
            } for product in products)
        }


class ProductView(View):

    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)
        if not product:
            return HttpResponseNotFound()
        return render(request, 'product.html', _get_context(self._get_context(request.user, product, getattr(product, 'foodproduct', None))))

    def _get_context(self, user, product, food_product, barcode_form=None):
        return {
            'product': {
                'id': product.id,
                'name': product.name,
                'barcode': product.barcode,
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
                'is_allowed': self._is_edit_allowed(user, product),
                'barcode_form': barcode_form or forms.BarcodeForm(initial={'barcode': product.barcode})
            }
        }

    def _is_edit_allowed(self, user, product):
        return not user.is_anonymous and ReceiptItem.objects.filter(product_alias__product=product, receipt__buyer=user).exists()

    @method_decorator(login_required)
    def post(self, request, product_id):
        product = Product.objects.get(id=product_id)
        if not product:
            return HttpResponseNotFound()
        if not self._is_edit_allowed(request.user, product):
            return HttpResponseForbidden()
        barcode_form = forms.BarcodeForm(request.POST)
        if barcode_form.is_valid():
            with transaction.atomic():
                original_product = Product.objects.filter(barcode=barcode_form.cleaned_data['barcode']).first()
                if original_product:
                    ProductAlias.objects.filter(product=product).update(product=original_product)
                    product.delete()
                    return HttpResponseRedirect(reverse('product', args=(original_product.id,)))
                else:
                    barcode_form.add_error(None, 'Штрихкод не найден')
        return render(request, 'product.html', _get_context(self._get_context(request.user, product, getattr(product, 'foodproduct', None), barcode_form)))


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
            'food_should_be': self._get_food_should_be(receipts),
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

    def _get_food_should_be(self, receipts):
        part = sum(receipt.protein + receipt.fat + receipt.carbohydrate for receipt in receipts) / 6
        return {
            'protein': part,
            'fat': part,
            'carbohydrate': part * 4,
        }


class TopReportView(View):

    TOP_SIZE = 10

    @method_decorator(login_required)
    def get(self, request):
        items = ReceiptItem.objects.filter(receipt__buyer=request.user,
                                           receipt__created__range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()))
        return render(request, 'reports/top.html', _get_context(
            self._get_context(self._get_top_by_calories(items), self._get_top_by_total(items), self._get_top_by_weight(items),
                              self._get_top_by_protein(items), self._get_top_by_fat(items), self._get_top_by_carbohydrate(items),
                              self._get_top_by_effectivity(items))
        ))

    def _get_top_by_calories(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if not product.is_food:
                continue
            if product not in products:
                products[product] = 0
            products[product] += item.calories / 1000
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_top_by_total(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if product not in products:
                products[product] = 0
            products[product] += item.total
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_top_by_weight(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if not product.is_food:
                continue
            if product not in products:
                products[product] = 0
            products[product] += item.quantity * product.foodproduct.weight / 1000
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_top_by_protein(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if not product.is_food:
                continue
            if product not in products:
                products[product] = 0
            products[product] += item.protein / 1000
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_top_by_fat(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if not product.is_food:
                continue
            if product not in products:
                products[product] = 0
            products[product] += item.fat / 1000
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_top_by_carbohydrate(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if not product.is_food:
                continue
            if product not in products:
                products[product] = 0
            products[product] += item.carbohydrate / 1000
        return sorted(products.items(), key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_top_by_effectivity(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            if not product.is_food:
                continue
            if product not in products:
                products[product] = []
            products[product].append(item.calories / float(item.total))
        products = ((product, sum(values) / len(values) / 1000) for product, values in products.items())
        return sorted(products, key=lambda item: item[1], reverse=True)[:self.TOP_SIZE]

    def _get_context(self, top_by_calories, top_by_total, top_by_weight, top_by_protein, top_by_fat, top_by_carbohydrate,
                     top_by_effectivity):
        def get_top(products):
            return tuple({
                'id': product.id,
                'name': product.name,
                'is_checked': product.is_checked,
                'value': value,
            } for product, value in products)
        return {
            'top_by_calories': get_top(top_by_calories),
            'top_by_total': get_top(top_by_total),
            'top_by_weight': get_top(top_by_weight),
            'top_by_protein': get_top(top_by_protein),
            'top_by_fat': get_top(top_by_fat),
            'top_by_carbohydrate': get_top(top_by_carbohydrate),
            'top_by_effectivity': get_top(top_by_effectivity)
        }


class SummaryView(View):

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

    def get(self, request):
        items = ReceiptItem.objects.filter(receipt__buyer=request.user,
                                           receipt__created__range=(datetime.utcnow() - timedelta(days=30), datetime.utcnow()))
        products = self._get_summary(items)
        sorting_key = request.GET.get('sort')
        if sorting_key in (item[0] for item in self.COLUMNS):
            products = sorted(products, key=lambda pair: getattr(pair[1], sorting_key) or 0, reverse=True)
        return render(request, 'reports/summary.html', _get_context(self._get_context(products, sorting_key)))

    def _get_summary(self, items):
        products = {}
        for item in items:
            product = item.product_alias.product
            stats = products.get(product)
            if stats is None:
                stats = self._FoodStats() if product.is_food else self._NonFoodStats()
                products[product] = stats
            stats.add(item)
        return tuple(products.items())

    def _get_context(self, products, sorting_key):
        return {
            'columns': self.COLUMNS,
            'sorting_key': sorting_key,
            'products': tuple({
                'id': product.id,
                'name': product.name,
                'is_food': product.is_food,
                'is_checked': product.is_checked,
                'protein': stats.protein,
                'fat': stats.fat,
                'carbohydrate': stats.carbohydrate,
                'calories': stats.calories,
                'total': stats.total
            } for product, stats in products)
        }