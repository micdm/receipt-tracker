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


class AddAliasForm(forms.Form):

    product_alias = forms.ModelChoiceField(None, label='', widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, product_id, *args, **kwargs):
        super(AddAliasForm, self).__init__(*args, **kwargs)
        self.fields['product_alias'].queryset = ProductAlias.objects.exclude(product=product_id).order_by('name')
        self.fields['product_alias'].label_from_instance = lambda alias: '%s (%s, %s)' % (alias.name, alias.seller.get_name(), alias.receiptitem_set.all().order_by('-receipt__created').first().price)


class RemoveAliasForm(forms.Form):

    product_alias_id = forms.IntegerField(widget=forms.HiddenInput())
