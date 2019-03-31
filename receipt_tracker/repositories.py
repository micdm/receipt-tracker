from datetime import datetime, timedelta
from typing import List, Optional

from django.db.transaction import atomic

from receipt_tracker.models import Product, ProductAlias, ReceiptItem, Receipt, NonFoodProduct


class ProductRepository:

    def get_all(self) -> List[Product]:
        # TODO: сортировка
        return Product.objects.all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return Product.objects.filter(id=product_id).first()

    @atomic
    def set_barcode(self, product_id: int, barcode: int) -> Optional[int]:
        product = self.get_by_id(product_id)
        original_product = Product.objects.filter(barcode=barcode).first()
        if original_product:
            ProductAlias.objects.filter(product=product).update(product=original_product)
            product.delete()
            return original_product.id
        return None

    @atomic
    def set_non_food(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if product.is_food:
            product.foodproduct.delete()
            NonFoodProduct.objects.create(product=product)
            return True
        return False


class ReceiptRepository:

    def get_last_by_buyer_id(self, buyer_id: int) -> List[Receipt]:
        now = datetime.utcnow()
        return Receipt.objects \
            .filter(buyer=buyer_id, created__range=(now - timedelta(days=30), now)) \
            .order_by('-created')


class ReceiptItemRepository:

    def get_last(self) -> List[ReceiptItem]:
        return ReceiptItem.objects.order_by('-receipt__created')[:50]

    def get_last_by_buyer_id(self, buyer_id: int) -> List[ReceiptItem]:
        now = datetime.utcnow()
        return ReceiptItem.objects.filter(receipt__buyer=buyer_id,
                                          receipt__created__range=(now - timedelta(days=30), now))

    def get_by_product_id(self, product_id: int) -> List[ReceiptItem]:
        return ReceiptItem.objects.filter(product_alias__product=product_id).order_by('-receipt__created')

    def is_exist_by_product_id_and_buyer_id(self, product_id: int, buyer_id: int) -> bool:
        return ReceiptItem.objects.filter(product_alias__product=product_id, receipt__buyer=buyer_id).exists()


product_repository = ProductRepository()
receipt_repository = ReceiptRepository()
receipt_item_repository = ReceiptItemRepository()
