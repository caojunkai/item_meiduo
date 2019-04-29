from django.conf.urls import url,include
from . import views

urlpatterns = [
    url('^areas/$',views.AreaView.as_view()),
]