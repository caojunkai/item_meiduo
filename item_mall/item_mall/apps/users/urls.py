from django.conf.urls import url,include
from . import views


urlpatterns = [
    # 注册
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.MobileCountView.as_view()),

url(r'^login/$', views.LoginView.as_view(), name='login'),
url(r'^$', views.IndexView.as_view(), name='index'),
    url('^logout/$', views.LogoutView.as_view()),

    url('^info/$', views.InfoView.as_view()),
url('^$', views.InfoView.as_view()),

]