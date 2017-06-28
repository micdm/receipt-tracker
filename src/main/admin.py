from django.contrib import admin
from main import models

admin.site.register(models.Seller)
admin.site.register(models.Product)
admin.site.register(models.ProductAlias)
admin.site.register(models.Receipt)
admin.site.register(models.ReceiptItem)
admin.site.register(models.AddReceiptTask)
