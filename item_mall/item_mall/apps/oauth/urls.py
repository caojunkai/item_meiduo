from django.conf.urls import url,include
from . import views


urlpatterns = [
url('^qq/login/$',views.QQurlView.as_view()),
url('^oauth_callback/$',views.QQopenidView.as_view()),
]


