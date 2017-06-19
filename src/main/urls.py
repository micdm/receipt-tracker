from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import logout

from main import views

urlpatterns = [
    url('', include('social_django.urls', namespace='social')),
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index, name='index'),
    url(r'^log_out$', logout, {'next_page': '/'}, name='logout'),
    url(r'^add_receipt$', views.add_receipt, name='add_receipt'),
    url(r'^receipt_added/(?P<fiscal_drive_number>\d+)-(?P<fiscal_document_number>\d+)-(?P<fiscal_sign>\d+)$', views.receipt_added, name='receipt_added'),
]
