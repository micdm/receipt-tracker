from django import forms

from main.models import ProductAlias


class QrForm(forms.Form):

    text = forms.CharField(label='Текст', widget=forms.TextInput(attrs={'autocomplete': 'off'}))


class ManualInputForm(forms.Form):

    fiscal_drive_number = forms.IntegerField(label='ФН')
    fiscal_document_number = forms.IntegerField(label='ФД')
    fiscal_sign = forms.IntegerField(label='ФП')


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
