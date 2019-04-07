from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from receipt_tracker.models import NonFoodProduct, Product, ProductAlias, Receipt, ReceiptItem, Seller


class SellerRepository:

    def get_or_create(self, individual_number: str, original_name: str) -> Seller:
        seller, _ = Seller.objects.get_or_create(individual_number=individual_number,
                                                 defaults={'original_name': original_name})
        return seller


class ProductRepository:

    def create(self) -> Product:
        return Product.objects.create()

    def get_all(self) -> List[Product]:
        # TODO: сортировка
        return Product.objects.all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return Product.objects.filter(id=product_id).first()

    def set_barcode(self, product_id: int, barcode: str) -> Optional[int]:
        product = self.get_by_id(product_id)
        original_product = Product.objects.filter(barcode=barcode).first()
        if not original_product:
            return None
        ProductAlias.objects.filter(product=product).update(product=original_product)
        product.delete()
        return original_product.id

    def set_non_food(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if not product.is_food:
            return False
        product.foodproduct.delete()
        NonFoodProduct.objects.create(product=product)
        return True


class ProductAliasRepository:

    def create(self, seller_id: int, product_id: int, name: str) -> ProductAlias:
        return ProductAlias.objects.create(seller_id=seller_id, product_id=product_id, name=name)

    def get_by_seller_and_name(self, seller_id: int, name: str) -> Optional[ProductAlias]:
        return ProductAlias.objects.filter(seller=seller_id, name=name).first()


class ReceiptRepository:

    def create(self, seller_id: int, buyer_id: int, created: datetime, fiscal_drive_number: str,
               fiscal_document_number: str, fiscal_sign: str) -> Receipt:
        return Receipt.objects.create(seller_id=seller_id, buyer_id=buyer_id, created=created,
                                      fiscal_drive_number=fiscal_drive_number,
                                      fiscal_document_number=fiscal_document_number, fiscal_sign=fiscal_sign)

    def get_by_buyer_id(self, buyer_id: int) -> List[Receipt]:
        return Receipt.objects.filter(buyer=buyer_id)

    def get_last_by_buyer_id(self, buyer_id: int) -> List[Receipt]:
        now = datetime.utcnow()
        return Receipt.objects \
            .filter(buyer=buyer_id, created__range=(now - timedelta(days=30), now)) \
            .order_by('-created')


class ReceiptItemRepository:

    def create(self, receipt_id: int, product_alias_id: int, price: Decimal, quantity: Decimal,
               total: Decimal) -> ReceiptItem:
        return ReceiptItem.objects.create(receipt_id=receipt_id, product_alias_id=product_alias_id, price=price,
                                          quantity=quantity, total=total)

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


seller_repository = SellerRepository()
product_repository = ProductRepository()
product_alias_repository = ProductAliasRepository()
receipt_repository = ReceiptRepository()
receipt_item_repository = ReceiptItemRepository()
