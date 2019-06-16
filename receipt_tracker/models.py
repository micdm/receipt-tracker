from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from django.contrib.auth import get_user_model
from django.core.validators import integer_validator
from django.db import models

User = get_user_model()


class Seller(models.Model):

    individual_number = models.CharField(max_length=15, unique=True, validators=[integer_validator])
    original_name: str = models.CharField(max_length=100)
    user_friendly_name: str = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f'Seller(name={self.name})'

    @property
    def name(self) -> str:
        if self.user_friendly_name:
            return self.user_friendly_name
        return self.original_name


class Product(models.Model):

    user_friendly_name: str = models.CharField(max_length=100, null=True, blank=True)
    barcode = models.CharField(max_length=20, null=True, blank=True, validators=[integer_validator])

    def __str__(self):
        return f'Product(name={self.name})'

    @property
    def name(self) -> str:
        if self.user_friendly_name:
            return self.user_friendly_name
        if self.aliases:
            return self.aliases[0].name
        return '?'

    @property
    def is_food(self) -> bool:
        return hasattr(self, 'foodproduct')

    @property
    def is_non_food(self) -> bool:
        return hasattr(self, 'nonfoodproduct')

    @property
    def is_checked(self) -> bool:
        return self.is_food or self.is_non_food

    @property
    def details(self) -> Optional[Union['FoodProduct', 'NonFoodProduct']]:
        if self.is_food:
            return self.foodproduct
        if self.is_non_food:
            return self.nonfoodproduct
        return None

    @property
    def aliases(self) -> List['ProductAlias']:
        return self.productalias_set.all()

    @property
    def last_buy(self) -> datetime:
        return Receipt.objects.filter(receiptitem__product_alias__product=self).order_by('-created')[0].created

    @property
    def last_price(self) -> Decimal:
        return ReceiptItem.objects.filter(product_alias__product=self).order_by('-receipt__created')[0].price

    def copy_from(self, product: 'Product') -> bool:
        changed = False
        for key in ('user_friendly_name', 'barcode'):
            if getattr(self, key) is None:
                value = getattr(product, key)
                if value is not None:
                    setattr(self, key, value)
                    changed = True
        return changed


class FoodProduct(models.Model):

    product = models.OneToOneField(Product, models.CASCADE)
    calories: int = models.PositiveIntegerField(help_text='На сто грамм')
    protein: Decimal = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    fat: Decimal = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    carbohydrate: Decimal = models.DecimalField(decimal_places=2, max_digits=4, help_text='На сто грамм')
    weight: int = models.PositiveSmallIntegerField(help_text='В граммах')

    def __str__(self):
        return f'FoodProduct(product={self.product}, weight={self.weight})'

    @property
    def total_calories(self) -> int:
        return round(self.calories * self.weight / 100)

    @property
    def total_protein(self) -> Decimal:
        return self.protein * self.weight / 100

    @property
    def total_fat(self) -> Decimal:
        return self.fat * self.weight / 100

    @property
    def total_carbohydrate(self) -> Decimal:
        return self.carbohydrate * self.weight / 100


class NonFoodProduct(models.Model):

    product = models.OneToOneField(Product, models.CASCADE)

    def __str__(self):
        return f'NonFoodProduct(product={self.product}'


class ProductAlias(models.Model):

    seller = models.ForeignKey(Seller, models.CASCADE)
    product: Product = models.ForeignKey(Product, models.CASCADE)
    name: str = models.CharField(max_length=100)

    def __str__(self):
        return f'ProductAlias(product={self.product}, name={self.name})'


class Receipt(models.Model):

    class Meta:
        unique_together = ('fiscal_drive_number', 'fiscal_document_number', 'fiscal_sign')

    seller = models.ForeignKey(Seller, models.CASCADE)
    buyer = models.ForeignKey(get_user_model(), models.CASCADE)
    created = models.DateTimeField()
    fiscal_drive_number = models.CharField(max_length=50, validators=[integer_validator])
    fiscal_document_number = models.CharField(max_length=50, validators=[integer_validator])
    fiscal_sign = models.CharField(max_length=50, validators=[integer_validator])

    def __str__(self):
        return f'Receipt(seller={self.seller}, created={self.created})'

    @property
    def items(self) -> List['ReceiptItem']:
        return self.receiptitem_set.order_by('product_alias__name')

    @property
    def protein(self) -> Optional[Decimal]:
        return self._get_food_value('protein')

    @property
    def fat(self) -> Optional[Decimal]:
        return self._get_food_value('fat')

    @property
    def carbohydrate(self) -> Optional[Decimal]:
        return self._get_food_value('carbohydrate')

    @property
    def calories(self) -> Optional[Decimal]:
        return self._get_food_value('calories')

    def _get_food_value(self, name) -> Optional[Decimal]:
        values = [value for value in (getattr(item, name) for item in self.items) if value is not None]
        if values:
            return sum(values)
        return None

    @property
    def non_checked_product_count(self) -> int:
        return sum(not item.is_product_checked for item in self.items)


class ReceiptItem(models.Model):

    receipt = models.ForeignKey(Receipt, models.CASCADE)
    product_alias: ProductAlias = models.ForeignKey(ProductAlias, models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    quantity = models.DecimalField(decimal_places=3, max_digits=6)
    total = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f'ReceiptItem(product_alias={self.product_alias}, quantity={self.quantity}, price={self.price})'

    @property
    def protein(self) -> Optional[Decimal]:
        return self._get_food_value('protein')

    @property
    def fat(self) -> Optional[Decimal]:
        return self._get_food_value('fat')

    @property
    def carbohydrate(self) -> Optional[Decimal]:
        return self._get_food_value('carbohydrate')

    @property
    def calories(self) -> Optional[Decimal]:
        return self._get_food_value('calories')

    def _get_food_value(self, name) -> Optional[Decimal]:
        product = self.product_alias.product
        if not product.is_food:
            return None
        return getattr(product.foodproduct, name) * product.foodproduct.weight / 100

    @property
    def is_product_checked(self) -> bool:
        return self.product_alias.product.is_checked
