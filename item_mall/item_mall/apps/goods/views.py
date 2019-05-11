from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from django.views import View

from item_mall.utils.meiduo_category import get_categories

from .models import GoodsCategory, SKU,GoodsVisitCount

from django.core.paginator import Paginator

from . import constants
from datetime import datetime

from django import http
import json
from item_mall.utils.breadcrumb import get_breadcrumb

from item_mall.utils.response_code import RETCODE
from django.contrib.auth import login
from django_redis import get_redis_connection

class ListView(View):
    def get(self,request,category_id,page_num):

        try:
            category3 = GoodsCategory.objects.get(pk = category_id)
        except:
            return render(request,'404.html')

        # -分类数据
        categories = get_categories()
        #面包屑导航
        # category2 = category3.parent
        # category1 = category2.parent
        #
        # print(category1.goodschannel_set.all())
        #
        # breadcrumb = {
        #     'cat1': {
        #         'name': category1.name,
        #         'url': category1.goodschannel_set.all()[0].url
        #     },
        #     'cat2': category2,
        #     'cat3': category3
        # }
        breadcrumb = get_breadcrumb(category3)



        #当前分类数据
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
        context = {
            'categories': categories,
            'breadcrumb': breadcrumb,
            'page_skus': page_skus,
            'category': category3,
            'sort': sort,
            'page_num': page_num,
            'total_page': paginator.num_pages,
        }
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

#详情页
class DetailView(View):
    def get(self,request,sku_id):
        try:
            sku = SKU.objects.get(id = sku_id)
        except:
            return render(request,'404.html')
        #三级分类
        category3 = sku.category
        #频道分类
        categories = get_categories()
        #面包屑导航
        breadcrumb = get_breadcrumb(category3)
        # 获取当前展示商品的规格信息
        sku_specs = sku.specs.order_by('spec_id')
        # 当前商品的规格选项添入列表
        sku_list = [info.option_id for info in sku_specs]
        print('--',sku_list)


        #获取标准商品表对象
        spu = sku.spu
        #标准商品（spu)到库存商品(sku)到商品规格sku_specs(specs)信息
        skus = spu.sku_set.filter(is_launched = True)
        #将每种商品的规格遍历出来 例如（13,20）（13,21）同为钻雕金  20 64g 21  128g
        sku_option_dict = {}
        for sku_info in  skus:
            sku_info_options = sku_info.specs.order_by('spec_id')
            sku_info_option_list = [option_info.option_id for option_info in sku_info_options]
            # 将选项列表为键，库存商品编号为值
            # tuple将列表转成元祖  因为字典的键必须为不可修改
            sku_option_dict[tuple(sku_info_option_list)] = sku_info.id


        #通过关系属性获取所有的规格
        specs = spu.specs.all()
        print('--a',specs)
        specs_list = []
        # 转换数据格式
        # 遍历规格
        for index,spec in enumerate(specs):

            spec_dict ={
                'name':spec.name,
                'options':[]
            }
            # 查询所有spec规格所有选项
            options = spec.options.all()
            # 将选项添加进列表
            for option in options:
               option_dict ={
                    'name':option.value,
                    'id':option.id
                }
                #复制当前库存商品的选项
               sku_option_list_temp = sku_list[:]
               print('===',sku_option_list_temp)
                #当前选项是否选中
               if option.id in sku_list:
                   option_dict['selected'] = True
               else:
                   option_dict['selected'] = False

               # 为选项指定库存商品编号
               sku_option_list_temp[index] = option.id
               ti = tuple(sku_option_list_temp)
               print(sku_option_list_temp)
               option_dict['sku_id'] = sku_option_dict.get(ti,0)
               spec_dict['options'].append(option_dict)

        # 列表里有多个字典（spec_dict）
            specs_list.append(spec_dict)



        context={
            'categories':categories,
            'breadcrumb':breadcrumb,
            'sku':sku,
            'spu':spu,
            'category_id':category3.id,
            'specs':specs_list
        }
        return render(request,'detail.html',context)


class DetailVisitView(View):
    def post(self,request,category_id):
        # 统计某天某个三级分类的访问次数
        now = datetime.now()

        date = '%d-%d-%d' % (now.year, now.month, now.day)

        try:
            category = GoodsVisitCount.objects.get(category_id=category_id, date=date)
        except:
            GoodsVisitCount.objects.create(category_id=category_id,count = 1)
        else:
            #查询到则加一
            category.count+=1
            category.save()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok'
        })
class HistoryView(View):
    #查询记录
    def get(self,request):
        user = request.user
        if not user.is_authenticated:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'用户未登录，不需要记录浏览商品'})
        redis_cli = get_redis_connection('history')
        key = 'history%d' %user.id
        sku_ids = redis_cli.lrange(key,0,-1)
        sku_ids =[int(sku_id) for sku_id in sku_ids]
        sku_dict_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id = sku_id)
            sku_dict_list.append({
                'id':sku_id,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'price':sku.price,
            })
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'skus': sku_dict_list
        })

    def post(self,request):
        sku_id = json.loads(request.body.decode()).get('sku_id')
        if not all([sku_id]):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'缺少库存商品编号'})
        user =request.user
        if not user.is_authenticated:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'用户未登录，不需要记录浏览商品'})
        try:
            sku =SKU.objects.get(id =sku_id)
        except:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '库存商品编号无效'})

        redis_cli = get_redis_connection('history')
        redis_pl = redis_cli.pipeline()
        key = 'history%d' %user.id
        #删除指定
        redis_pl.lrem(key,0,sku_id)
        #添加
        redis_pl.lpush(key,sku_id)
        #限制
        redis_pl.ltrim(key,0,4)
        #执行与redis服务器的交互
        redis_pl.execute()
        # 响应
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok'
        })







