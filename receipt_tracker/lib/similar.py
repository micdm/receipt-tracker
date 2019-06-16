from dataclasses import dataclass
from logging import getLogger
from typing import Sequence

from numpy import nonzero
from sklearn.feature_extraction.text import TfidfVectorizer

from receipt_tracker.models import Product

logger = getLogger(__name__)


def normalize(text: str) -> str:
    return text.lower()


@dataclass
class SimilarProduct:

    product: Product
    confidence: float


class SimilarProductFinder:

    MIN_CONFIDENCE = 0.3
    RESULT_COUNT = 5

    def __init__(self, products: Sequence[Product]):
        self._products = products
        self._vectorizer = TfidfVectorizer()
        self._vectors = self._vectorizer.fit_transform(normalize(product.name) for product in products)

    def find(self, name: str) -> Sequence[SimilarProduct]:
        vector = self._vectorizer.transform([normalize(name)])
        dot = self._vectors.dot(vector.toarray()[0])

        similars = [SimilarProduct(self._products[index], round(dot[index], 6)) for index in nonzero(dot)[0]
                    if self._products[index].name != name and dot[index] >= self.MIN_CONFIDENCE]
        similars.sort(key=lambda item: item.confidence, reverse=True)

        return similars[:self.RESULT_COUNT]
