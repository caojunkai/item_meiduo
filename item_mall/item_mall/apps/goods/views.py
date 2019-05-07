from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from django.views import View

from item_mall.utils.meiduo_category import get_categories

from .models import GoodsCategory, SKU

from django.core.paginator import Paginator

from . import constants

from django import http

from item_mall.utils.response_code import RETCODE
from django.contrib.auth import login

class ListView(LoginRequiredMixin,View):
    def get(self,request,category_id,page_num):
        # user = request.user
        try:
            category3 = GoodsCategory.objects.get(pk = category_id)
        except:
            return render(request,'404.html')

        # -分类数据
        categories = get_categories()

        category2 = category3.parent
        category1 = category2.parent

        print(category1.goodschannel_set.all())

        breadcrumb = {
            'cat1': {
                'name': category1.name,
                'url': category1.goodschannel_set.all()[0].url
            },
            'cat2': category2,
            'cat3': category3
        }
        skus =category3.sku_set.filter(is_launched = True)

        # print(skus)

        # -排序
        sort = request.GET.get('sort', 'default')
        if sort == 'hot':  # 人气hot
            skus = skus.order_by('-sales')
        elif sort == 'price':  # 价格price
            skus = skus.order_by('price')
        else:  # 默认default
            skus = skus.order_by('-id')

            # - 分页
            # 创建分页对象
        paginator = Paginator(skus,constants.LIST_PER_PAGE)
        #获取指定页的数据
        page_skus = paginator.page(page_num)


        user = request.user

        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'page_skus': page_skus,
            'category': category3,
            'sort': sort,
            'page_num': page_num,
            'total_page': paginator.num_pages,
            'username':user.username
        }

        login(request, user)
        return render(request, 'list.html', context)

class HotView(View):

    def get(self, request, category_id):
        # 查询2个最热销的商品
        skus = SKU.objects.filter(is_launched=True, category_id=category_id).order_by('-sales')[0:2]
        #格式转换
        sku_list = []
        for sku in skus:
            sku_list.append({
                 'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })
    #响应
        return  http.JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'ok',
            'hot_sku_list':sku_list
        })
