from django import forms

from main.models import ProductAlias


class _BootstrapTextarea(forms.Textarea):

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get("attrs") or {}
        attrs["class"] = "form-control"
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)


class _BootstrapTextInput(forms.TextInput):

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get("attrs") or {}
        attrs["class"] = "form-control"
        kwargs["attrs"] = attrs
        super().__init__(*args, **kwargs)


class QrForm(forms.Form):

    text = forms.CharField(label='Текст', widget=_BootstrapTextarea(attrs={'autocomplete': 'off', 'rows': 4}))


class ManualInputForm(forms.Form):

    fiscal_drive_number = forms.IntegerField(label='ФН', widget=_BootstrapTextInput())
    fiscal_document_number = forms.IntegerField(label='ФД', widget=_BootstrapTextInput())
    fiscal_sign = forms.IntegerField(label='ФП', widget=_BootstrapTextInput())
    total_sum = forms.DecimalField(label='Итого', required=False, widget=_BootstrapTextInput())


class PhotoForm(forms.Form):

    photo = forms.ImageField(label='Фото с QR-кодом')
