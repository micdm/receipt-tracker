from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from receipt_tracker.views import general, reports

urlpatterns = (
    path('admin/', admin.site.urls),
    path('', general.index_view, name='index'),
    path('logout/', LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    path('receipts/add/', general.add_receipt_view, name='add-receipt'),
    path('receipts/added/', general.receipt_added_view, name='receipt-added'),
    path('products/', general.products_view, name='products'),
    path('product/<int:product_id>/', general.product_view, name='product'),
    path('product/<int:product_id>/merge/<int:another_product_id>', general.merge_product_view, name='merge-product'),
    path('reports/value/', reports.value_report_view, name='value-report'),
    path('reports/top/', reports.top_report_view, name='top-report'),
    path('reports/summary/', reports.summary_report_view, name='summary-report'),
)
