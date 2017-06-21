from django import forms


class QrForm(forms.Form):

    text = forms.CharField(label='Текст', widget=forms.TextInput(attrs={'autocomplete': 'off'}))


class ManualInputForm(forms.Form):

    fiscal_drive_number = forms.IntegerField(label='ФН')
    fiscal_document_number = forms.IntegerField(label='ФД')
    fiscal_sign = forms.IntegerField(label='ФП')


class PhotoForm(forms.Form):

    photo = forms.ImageField(label='Фото с QR-кодом')
