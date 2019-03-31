from datetime import datetime

from mixer.backend.django import mixer as default_mixer
from pytest import fixture

from receipt_tracker.models import FoodProduct, NonFoodProduct, Product, ProductAlias, Receipt, ReceiptItem, Seller, \
    User


@fixture
def mixer():
    return default_mixer


@fixture
def guest_client(client):
    return client


@fixture
def authorized_client(client, user):
    client.force_login(user)
    return client


@fixture
def user(mixer):
    user = mixer.blend(User)
    user.set_password('password')
    user.save()
    return user


@fixture
def seller(mixer):
    return mixer.blend(Seller)


@fixture
def product(mixer):
    return mixer.blend(Product)


@fixture
def product_with_barcode(mixer):
    return mixer.blend(Product, barcode='1')


@fixture
def food_product(mixer, product):
    return mixer.blend(FoodProduct, product=product)


@fixture
def non_food_product(mixer, product):
    return mixer.blend(NonFoodProduct, product=product)


@fixture
def product_alias(mixer, seller, product):
    return mixer.blend(ProductAlias, seller=seller, product=product)


@fixture
def receipt(mixer, seller, user):
    return mixer.blend(Receipt, seller=seller, buyer=user, created=datetime.utcnow())


@fixture
def receipt_item(mixer, receipt, product_alias):
    return mixer.blend(ReceiptItem, receipt=receipt, product_alias=product_alias)
