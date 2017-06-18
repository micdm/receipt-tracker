from django.contrib import admin
from main import models


@admin.register(models.Seller)
class SellerAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ReceiptItem)
class ReceiptItemAdmin(admin.ModelAdmin):
    pass
