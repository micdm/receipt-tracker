from django.contrib.auth import get_user_model
from django.db import models


class Seller(models.Model):

    individual_number = models.PositiveIntegerField(unique=True)
    original_name = models.CharField(max_length=100)
    user_friendly_name = models.CharField(max_length=100, null=True)

    @property
    def name(self):
        return self.user_friendly_name or self.original_name

    def __str__(self):
        return self.name


class Product(models.Model):

    user_friendly_name = models.CharField(max_length=100, null=True, blank=True)
    barcode = models.PositiveIntegerField(null=True, blank=True)

    @property
    def name(self):
        return self.user_friendly_name or str(self.productalias_set.all()[0])

    @property
    def is_food(self):
        return hasattr(self, 'foodproduct')

    @property
    def is_non_food(self):
        return hasattr(self, 'nonfoodproduct')

    @property
    def is_checked(self):
        return self.is_food or self.is_non_food

    def __str__(self):
        return self.name


class FoodProduct(models.Model):

    product = models.OneToOneField(Product)
    calories = models.PositiveIntegerField(help_text='На сто грамм')
    protein = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    fat = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    carbohydrate = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    weight = models.PositiveSmallIntegerField(help_text='В граммах')

    def __str__(self):
        return '%s (%sг)' % (str(self.product), self.weight)


class NonFoodProduct(models.Model):

    product = models.OneToOneField(Product)

    def __str__(self):
        return str(self.product)


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
