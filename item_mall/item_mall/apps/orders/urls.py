from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^orders/settlement/$',views.SettlementView.as_view()),
    url(r'^orders/commit/$', views.OrderCommitView.as_view()),
    url(r'^orders/success/$',views.SuccessView.as_view()),
    url('^orders/info/(?P<page_num>\d+)/$', views.OrderListView.as_view()),


]