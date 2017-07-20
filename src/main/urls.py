from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import logout

from main import views

urlpatterns = (
    url('', include('social_django.urls', namespace='social')),
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^log_out$', logout, {'next_page': '/'}, name='logout'),
    url(r'^add_receipt$', views.AddReceiptView.as_view(), name='add_receipt'),
    url(r'^receipt_added$', views.ReceiptAddedView.as_view(), name='receipt_added'),
    url(r'^product/(?P<product_id>\d+)$', views.ProductView.as_view(), name='product'),
    url(r'^reports/value$', views.ValueReportView.as_view(), name='value_report'),
    url(r'^reports/top', views.TopReportView.as_view(), name='top_report'),
    url(r'^reports/summary', views.SummaryView.as_view(), name='summary_report'),
)
