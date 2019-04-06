from django import forms


class _BootstrapTextarea(forms.Textarea):

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs') or {}
        attrs['class'] = 'form-control'
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class _BootstrapTextInput(forms.TextInput):

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs') or {}
        attrs['class'] = 'form-control'
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class _BootstrapNumberInput(forms.NumberInput):

    def __init__(self, *args, **kwargs):
        attrs = kwargs.get('attrs') or {}
        attrs['class'] = 'form-control'
        kwargs['attrs'] = attrs
        super().__init__(*args, **kwargs)


class QrForm(forms.Form):

    text = forms.CharField(label='Текст', widget=_BootstrapTextarea(attrs={'autocomplete': 'off', 'rows': 4}))


class BarcodeForm(forms.Form):

    barcode = forms.IntegerField(label='Штрихкод', widget=_BootstrapNumberInput())
