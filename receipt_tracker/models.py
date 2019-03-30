from decimal import Decimal

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

    @property
    def last_buy(self):
        return Receipt.objects.filter(receiptitem__product_alias__product=self).order_by('-created')[0].created

    @property
    def last_price(self):
        return ReceiptItem.objects.filter(product_alias__product=self).order_by('-receipt__created')[0].price

    def __str__(self):
        return self.name


class FoodProduct(models.Model):

    product = models.OneToOneField(Product, models.CASCADE)
    calories: int = models.PositiveIntegerField(help_text='На сто грамм')
    protein: Decimal = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    fat: Decimal = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    carbohydrate: Decimal = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    weight: int = models.PositiveSmallIntegerField(help_text='В граммах')

    @property
    def total_calories(self):
        return self.calories * self.weight / 100

    @property
    def total_protein(self):
        return self.protein * self.weight / 100

    @property
    def total_fat(self):
        return self.fat * self.weight / 100

    @property
    def total_carbohydrate(self):
        return self.carbohydrate * self.weight / 100

    def __str__(self):
        return '%s (%sг)' % (str(self.product), self.weight)


class NonFoodProduct(models.Model):

    product = models.OneToOneField(Product, models.CASCADE)

    def __str__(self):
        return str(self.product)


class ProductAlias(models.Model):

    seller = models.ForeignKey(Seller, models.CASCADE)
    product: Product = models.ForeignKey(Product, models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Receipt(models.Model):

    class Meta:
        unique_together = ('fiscal_drive_number', 'fiscal_document_number', 'fiscal_sign')

    seller = models.ForeignKey(Seller, models.CASCADE)
    buyer = models.ForeignKey(get_user_model(), models.CASCADE)
    created = models.DateTimeField()
    fiscal_drive_number = models.BigIntegerField()
    fiscal_document_number = models.BigIntegerField()
    fiscal_sign = models.BigIntegerField()

    def __str__(self):
        return '%s@%s' % (self.seller, self.created)

    @property
    def items(self):
        return self.receiptitem_set.all()

    @property
    def protein(self):
        return self._get_food_value('protein')

    @property
    def fat(self):
        return self._get_food_value('fat')

    @property
    def carbohydrate(self):
        return self._get_food_value('carbohydrate')

    @property
    def calories(self):
        return self._get_food_value('calories')

    def _get_food_value(self, name):
        return sum(filter(bool, (getattr(item, name) for item in self.items)))

    @property
    def non_checked_product_count(self):
        return sum(not item.is_product_checked for item in self.items)


class ReceiptItem(models.Model):

    receipt = models.ForeignKey(Receipt, models.CASCADE)
    product_alias: ProductAlias = models.ForeignKey(ProductAlias, models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    quantity = models.DecimalField(decimal_places=3, max_digits=6)
    total = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return '%s x%s по %s' % (self.product_alias, self.quantity, self.price)

    @property
    def protein(self):
        return self._get_food_value('protein')

    @property
    def fat(self):
        return self._get_food_value('fat')

    @property
    def carbohydrate(self):
        return self._get_food_value('carbohydrate')

    @property
    def calories(self):
        return self._get_food_value('calories')

    def _get_food_value(self, name):
        product = self.product_alias.product
        if not product.is_food:
            return None
        return getattr(product.foodproduct, name) * product.foodproduct.weight / 100

    @property
    def is_product_checked(self):
        return self.product_alias.product.is_checked


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
    buyer = models.ForeignKey(get_user_model(), models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)

    def __str__(self):
        return '%s-%s-%s' % (self.fiscal_drive_number, self.fiscal_document_number, self.fiscal_sign)
