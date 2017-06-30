from django.contrib.auth import get_user_model
from django.db import models


class Seller(models.Model):

    individual_number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.name

    def get_name(self):
        return self.short_name or self.name


class Product(models.Model):

    barcode = models.PositiveIntegerField(null=True)

    def __str__(self):
        return str(self.productalias_set.all()[0])


class ProductAlias(models.Model):

    seller = models.ForeignKey(Seller)
    product = models.ForeignKey(Product)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Receipt(models.Model):

    class Meta:
        unique_together = ('fiscal_drive_number', 'fiscal_document_number', 'fiscal_sign')

    seller = models.ForeignKey(Seller)
    buyer = models.ForeignKey(get_user_model())
    created = models.DateTimeField()
    fiscal_drive_number = models.BigIntegerField()
    fiscal_document_number = models.BigIntegerField()
    fiscal_sign = models.BigIntegerField()

    def __str__(self):
        return '%s@%s' % (self.seller, self.created)


class ReceiptItem(models.Model):

    receipt = models.ForeignKey(Receipt)
    product_alias = models.ForeignKey(ProductAlias)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    quantity = models.DecimalField(decimal_places=3, max_digits=6)
    total = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return '%s x%s по %s' % (self.product_alias, self.quantity, self.price)


class AddReceiptTask(models.Model):

    class Meta:
        unique_together = ('fiscal_drive_number', 'fiscal_document_number', 'fiscal_sign')

    STATUS_NEW = 0
    STATUS_COMPLETE = 1
    STATUS_INCOMPLETE = 2

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новое'),
        (STATUS_COMPLETE, 'Выполнено'),
        (STATUS_INCOMPLETE, 'Не выполнено'),
    )

    fiscal_drive_number = models.BigIntegerField()
    fiscal_document_number = models.BigIntegerField()
    fiscal_sign = models.BigIntegerField()
    total_sum = models.DecimalField(decimal_places=2, max_digits=10, null=True)
    buyer = models.ForeignKey(get_user_model())
    created = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)

    def __str__(self):
        return '%s-%s-%s' % (self.fiscal_drive_number, self.fiscal_document_number, self.fiscal_sign)
