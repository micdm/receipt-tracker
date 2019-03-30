from typing import List

from receipt_tracker.models import ReceiptItem, Product


class ProductRepository:

    def get_all(self) -> List[Product]:
        # TODO: сортировка
        return Product.objects.all()


class ReceiptItemRepository:

    def get_last(self) -> List[ReceiptItem]:
        return ReceiptItem.objects.order_by('-receipt__created')[:50]


product_repository = ProductRepository()
receipt_item_repository = ReceiptItemRepository()
