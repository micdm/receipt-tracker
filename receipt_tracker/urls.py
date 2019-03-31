from django.conf.urls import include
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from receipt_tracker import views

urlpatterns = (
    path('', include('social_django.urls', namespace='social')),
    path('admin/', admin.site.urls),
    path('', views.index_view, name='index'),
    path('log_out/', LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    path('receipts/add/', views.add_receipt_view, name='add-receipt'),
    path('receipts/added/', views.receipt_added_view, name='receipt-added'),
    path('products/', views.products_view, name='products'),
    path('product/<int:product_id>/', views.product_view, name='product'),
    path('reports/value/', views.value_report_view, name='value-report'),
    path('reports/top/', views.top_report_view, name='top-report'),
    path('reports/summary/', views.summary_report_view, name='summary-report'),
)
