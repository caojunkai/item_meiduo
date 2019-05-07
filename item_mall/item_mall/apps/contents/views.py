from django.shortcuts import render
from django.views import View
from .models import ContentCategory, Content
from item_mall.utils.meiduo_category import get_categories
# Create your views here.

class IndexView(View):
    def get(self,request):
        categories = get_categories()

        categorys = ContentCategory.objects.all()
        dict = {}
        for category in categorys:
            dict[category.key] = category.content_set.filter(status=True).order_by('sequence')
        context = {
            'categories': categories,
            'contents': dict
        }

        return render(request, 'index.html', context)