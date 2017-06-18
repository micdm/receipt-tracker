from django.conf.urls import url
from django.contrib import admin
from main import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index, name='index'),
    url(r'^add_receipt$', views.add_receipt, name='add_receipt'),
    url(r'^receipt_added/(?P<fiscal_drive_number>\d+)-(?P<fiscal_document_number>\d+)-(?P<fiscal_sign>\d+)$', views.receipt_added, name='receipt_added'),
]
