from datetime import datetime, timezone, timedelta
import decimal
from http import HTTPStatus
import re
import subprocess
import time
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, reverse, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseBadRequest
import requests
from logging import getLogger
from main.models import *
from main import forms


logger = getLogger(__name__)


def index(request):
    receipt_items = ReceiptItem.objects.order_by('-receipt__created')[:20]
    return render(request, 'index.html', {'receipt_items': receipt_items})


@login_required
def add_receipt(request):
    if request.method == 'POST' and 'qr' in request.POST:
        qr_form = forms.QrForm(request.POST)
        if qr_form.is_valid():
            try:
                params = _get_receipt_params_from_qr(qr_form.cleaned_data['text'])
                data = _get_receipt_json(*params)
                receipt = _save_receipt(data['document']['receipt'], request.user)
                return HttpResponseRedirect(reverse('receipt_added', kwargs={
                    'fiscal_drive_number': receipt.fiscal_drive_number,
                    'fiscal_document_number': receipt.fiscal_document_number,
                    'fiscal_sign': receipt.fiscal_sign
                }))
            except Exception as e:
                logger.debug('Cannot add receipt: %s', e)
                qr_form.add_error(None, 'Не удалось добавить чек: %s' % e)
    else:
        qr_form = forms.QrForm()
    if request.method == 'POST' and 'manual' in request.POST:
        manual_input_form = forms.ManualInputForm(request.POST)
        if manual_input_form.is_valid():
            try:
                data = _get_receipt_json(manual_input_form.cleaned_data['fiscal_drive_number'],
                                         manual_input_form.cleaned_data['fiscal_document_number'],
                                         manual_input_form.cleaned_data['fiscal_sign'])
                receipt = _save_receipt(data['document']['receipt'], request.user)
                return HttpResponseRedirect(reverse('receipt_added', kwargs={
                    'fiscal_drive_number': receipt.fiscal_drive_number,
                    'fiscal_document_number': receipt.fiscal_document_number,
                    'fiscal_sign': receipt.fiscal_sign
                }))
            except Exception as e:
                logger.debug('Cannot add receipt: %s', e)
                manual_input_form.add_error(None, 'Не удалось добавить чек: %s' % e)
    else:
        manual_input_form = forms.ManualInputForm()
    if request.method == 'POST' and 'photo' in request.POST:
        photo_form = forms.PhotoForm(request.POST, request.FILES)
        if photo_form.is_valid():
            try:
                params = _get_receipt_params_from_photo(photo_form.cleaned_data['photo'])
                data = _get_receipt_json(*params)
                receipt = _save_receipt(data['document']['receipt'], request.user)
                return HttpResponseRedirect(reverse('receipt_added', kwargs={
                    'fiscal_drive_number': receipt.fiscal_drive_number,
                    'fiscal_document_number': receipt.fiscal_document_number,
                    'fiscal_sign': receipt.fiscal_sign
                }))
            except Exception as e:
                logger.debug('Cannot add receipt: %s', e)
                photo_form.add_error(None, 'Не удалось добавить чек: %s' % e)
    else:
        photo_form = forms.PhotoForm()
    return render(request, 'add_receipt.html', {
        'qr_form': qr_form,
        'manual_input_form': manual_input_form,
        'photo_form': photo_form
    })


def _get_receipt_params_from_qr(text):
    try:
        return tuple(re.search(pattern, text).group(1) for pattern in (r'fn=(\d+)', r'i=(\d+)', r'fp=(\d+)'))
    except Exception:
        raise Exception('не удалось разобрать QR-текст')


def _get_receipt_params_from_photo(photo):
    try:
        output = subprocess.run(('zbarimg', '-q', '--raw', photo.temporary_file_path()), stdout=subprocess.PIPE,
                                check=True).stdout.decode('utf-8')
        return _get_receipt_params_from_qr(output)
    except Exception as e:
        raise Exception('не удалось распознать QR-код на фотографии: %s' % e)


def _get_receipt_json(fiscal_drive_number, fiscal_document_number, fiscal_sign):
    response = requests.get('http://proverkacheka.nalog.ru:8888/v1/inns/*/kkts/*/fss/%s/tickets/%s?fiscalSign=%s&sendToEmail=no' % (fiscal_drive_number, fiscal_document_number, fiscal_sign),
                            auth=(settings.CHECKER_LOGIN, settings.CHECKER_PASSWORD),
                            headers = {
                                'Device-Id': settings.CHECKER_DEVICE_ID,
                                'Device-OS': settings.CHECKER_DEVICE_OS,
                            })
    if response.status_code == HTTPStatus.ACCEPTED:
        time.sleep(3)
        return _get_receipt_json(fiscal_drive_number, fiscal_document_number, fiscal_sign)
    if response.status_code != HTTPStatus.OK:
        raise Exception('код ответа сервера %s' % response.status_code)
    result = response.json()
    logger.debug('Receipt JSON is %s', result)
    return result


def _save_receipt(data, user):
    if Receipt.objects.filter(fiscal_drive_number=data['fiscalDriveNumber'], fiscal_document_number=data['fiscalDocumentNumber'],
                              fiscal_sign=data['fiscalSign']).exists():
        raise Exception('чек уже добавлен')
    with transaction.atomic():
        seller = Seller.objects.get_or_create(individual_number=data['userInn'], defaults={'name': data['user']})[0]
        receipt = Receipt.objects.create(seller=seller, buyer=user,
                                         created=datetime.strptime(data['dateTime'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone(timedelta(hours=4))).astimezone(timezone.utc),
                                         fiscal_drive_number=data['fiscalDriveNumber'], fiscal_document_number=data['fiscalDocumentNumber'],
                                         fiscal_sign=data['fiscalSign'])
        for item in data['items']:
            if 'barcode' in item:
                product = Product.objects.get_or_create(barcode=item['barcode'])[0]
                product_alias = ProductAlias.objects.get_or_create(seller=seller, product=product, name=item['name'])[0]
            else:
                product_alias = ProductAlias.objects.filter(seller=seller, name=item['name']).first()
                if not product_alias:
                    product = Product.objects.create()
                    product_alias = ProductAlias.objects.create(seller=seller, product=product, name=item['name'])
            ReceiptItem.objects.create(receipt=receipt, product_alias=product_alias, price=decimal.Decimal(item['price'] / 100),
                                       quantity=decimal.Decimal(item['quantity']), total=decimal.Decimal(item['sum'] / 100))
    return receipt


@login_required
def receipt_added(request, fiscal_drive_number, fiscal_document_number, fiscal_sign):
    receipt = Receipt.objects.filter(fiscal_drive_number=fiscal_drive_number, fiscal_document_number=fiscal_document_number,
                                     fiscal_sign=fiscal_sign).first()
    if receipt is None:
        return HttpResponseBadRequest()
    return render(request, 'receipt_added.html', {'receipt': receipt})


def product(request, product_alias_id):
    product_alias = get_object_or_404(ProductAlias, pk=product_alias_id)
    return render(request, 'product.html', {'product_alias': product_alias})
