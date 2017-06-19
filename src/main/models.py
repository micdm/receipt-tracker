from django.contrib.auth import get_user_model
from django.db import models


class Seller(models.Model):

    individual_number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):

    class Meta:
        unique_together = ('seller', 'name')

    seller = models.ForeignKey(Seller)
    name = models.CharField(max_length=100)
    barcode = models.PositiveIntegerField(null=True)

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
    product = models.ForeignKey(Product)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    quantity = models.DecimalField(decimal_places=3, max_digits=6)
    total = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return '%s x%s по %s' % (self.product, self.quantity, self.price)
