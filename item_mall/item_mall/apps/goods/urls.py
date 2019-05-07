from django.conf.urls import url

from . import views

urlpatterns=[
    url('list/(?P<category_id>\d+)/(?P<page_num>\d+)/', views.ListView.as_view()),

    url('^hot/(?P<category_id>\d+)/$', views.HotView.as_view()),

]
