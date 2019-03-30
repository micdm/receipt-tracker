from django import forms
from django.contrib import admin

from receipt_tracker import models

admin.site.register(models.Seller)
admin.site.register(models.ProductAlias)
admin.site.register(models.Receipt)
admin.site.register(models.ReceiptItem)


def _get_boolean_field(short_description, getter):
    setattr(getter, 'short_description',  short_description)
    setattr(getter, 'boolean', True)
    return getter


class FoodProductInlineAdmin(admin.StackedInline):

    model = models.FoodProduct


class NonFoodProductInlineAdmin(admin.StackedInline):

    model = models.NonFoodProduct


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):

    class ProductModelForm(forms.ModelForm):
        class Meta:
            model = models.Product
            fields = '__all__'
        make_non_food = forms.BooleanField(required=False)

    inlines = (FoodProductInlineAdmin, NonFoodProductInlineAdmin)
    list_display = ('name', _get_boolean_field('Is checked', lambda model: model.is_checked))
    search_fields = ('user_friendly_name', 'productalias__name')

    def get_form(self, request, obj=None, **kwargs):
        return self.ProductModelForm

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['make_non_food']:
            if obj.is_food:
                obj.foodproduct.delete()
            models.NonFoodProduct.objects.create(product=obj)
        super(ProductAdmin, self).save_model(request, obj, form, change)
