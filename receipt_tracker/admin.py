from django import forms
from django.contrib import admin

from receipt_tracker.models import FoodProduct, NonFoodProduct, Product, ProductAlias, Receipt, ReceiptItem, Seller
from receipt_tracker.repositories import product_repository

admin.site.register(Seller)
admin.site.register(ProductAlias)
admin.site.register(Receipt)
admin.site.register(ReceiptItem)


class FoodProductInlineAdmin(admin.StackedInline):

    model = FoodProduct


class NonFoodProductInlineAdmin(admin.StackedInline):

    model = NonFoodProduct


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    class ProductModelForm(forms.ModelForm):
        class Meta:
            model = Product
            fields = '__all__'

        make_non_food = forms.BooleanField(required=False)

    inlines = (FoodProductInlineAdmin, NonFoodProductInlineAdmin)
    list_display = ('name', '_is_checked')
    search_fields = ('user_friendly_name', 'productalias__name')

    def _is_checked(self, product: Product):
        return product.is_checked
    _is_checked.short_description = 'Is checked'
    _is_checked.boolean = True

    def get_form(self, request, obj=None, **kwargs):
        return self.ProductModelForm

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['make_non_food']:
            product_repository.set_non_food(obj.id)
        super(ProductAdmin, self).save_model(request, obj, form, change)
