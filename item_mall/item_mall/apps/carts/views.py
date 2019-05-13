from django.shortcuts import render
from django.views import View
import json
from django import http
from item_mall.utils.response_code import RETCODE
from goods.models import SKU
from django_redis import get_redis_connection
from item_mall.utils import item_mall_json
from . import constants


# Create your views here.

class CartView(View):
    def post(self, request):
        # 接受数据
        param_dict = json.loads(request.body.decode())
        sku_id = param_dict.get('sku_id')
        count = param_dict.get('count')
        # 验证数据
        if not all([sku_id, count]):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '参数不完整'
            })
        # 验证sku_id是否合法
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '库存商品编号无效',
            })
        # count 合法性
        try:
            count = int(count)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '数量无效'
            })
        if count <= 0:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '数量应大于0'
            })
        # 判断库存
        if sku.stock < count:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '库存不足'
            })
        # 处理
        user = request.user
        response = http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok'
        })
        if user.is_authenticated:
            # 已登录则存redis里
            redis_cli = get_redis_connection('carts')
            redis_pl = redis_cli.pipeline()
            redis_pl.hset('cart%d' % user.id, sku_id, count)
            # 向set中保存sku_id
            redis_pl.sadd('selected%d' % user.id, sku_id)
            redis_pl.execute()
        else:
            # 未登录存cookie
            # 限读取cokkie中的购物车数据
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                cart_dict = {}
            else:
                cart_dict = item_mall_json.loads(cart_str)
            # 2.增加新的商品信息
            if sku_id not in cart_dict:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': True
                }
            else:
                # 存在则增加数量
                cart_dict[sku_id]['count'] = cart_dict[sku_id]['count'] + count
            # 保存
            cart_str = item_mall_json.dumps(cart_dict)
            response.set_cookie('cart', cart_str, max_age=constants.CART_EXPIRES)

        return response

    def get(self, request):
        # 显示购物车内容
        user = request.user
        cart_dict = {}
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            # 取hash中的sku_id,count
            cart_redis_dict = redis_cli.hgetall('cart%d' % user.id)
            # set中的sku_id
            selected_ids = redis_cli.smembers('selected%d' % user.id)
            # 将bytes转成int转成前段需要的格式放入cart_dict
            for sku_id, count in cart_redis_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_ids
                }
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                return render(request, 'cart.html', {'cart_skus': []})
            cart_dict = item_mall_json.loads(cart_str)
        # 查询库存商品，转换成前端需要的格式
        # cart_dict.keys()====>[1,2,3] select * from sku where id in [1,2,3]
        skus = SKU.objects.filter(pk__in=cart_dict.keys())
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),  # js中没有Decimal类型，所以需要转字符串
                'count': cart_dict[sku.id]['count'],
                'selected': str(cart_dict[sku.id]['selected'])  # js中的bool类型是true、false，而python中为True、False
            })
        context = {
            'cart_skus': sku_list
        }
        return render(request, 'cart.html', context)

    def put(self, request):
        # 修改购物车
        # 接收
        params_dict = json.loads(request.body.decode())
        sku_id = params_dict.get('sku_id')
        count = params_dict.get('count')
        selected = params_dict.get('selected')
        # 验证，比post多了个selected的验证
        if not all([sku_id, count]):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '参数不完整'
            })
        # 验证sku_id是否合法
        try:
            sku = SKU.objects.get(id=sku_id, is_launched=True)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '库存商品编号无效',
            })
        # count 合法性
        try:
            count = int(count)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '数量无效'
            })
        if count <= 0:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '数量应大于0'
            })
        # 判断库存
        if sku.stock < count:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '库存不足'
            })
        # selected的合法性 isinstance判断是否是一个已知的类型
        if not isinstance(selected, bool):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '选中状态错误'
            })
        # 处理
        user = request.user
        response = http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'cart_sku': {
                'id': sku_id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'selected': str(selected)
            }
        })
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            redis_pl = redis_cli.pipeline()
            # 修改hash中的数据
            redis_pl.hset('cart%d' % user.id, sku_id, count)
            if selected:
                redis_pl.sadd('selected%d' % user.id, sku_id)
            else:
                redis_pl.srem('selected%d' % user.id, sku_id)
            redis_pl.execute()
        else:
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                cart_dict = {}
            else:
                cart_dict = item_mall_json.loads(cart_str)
                # 修改数据
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            cart_str = item_mall_json.dumps(cart_dict)
            response.set_cookie('cart', cart_str, max_age=constants.CART_EXPIRES)
        return response

    def delete(self, request):
        # 接受
        param_dict = json.loads(request.body.decode())
        sku_id = param_dict.get('sku_id')
        if not all([sku_id]):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '参数不完整'
            })
        try:
            sku = SKU.objects.get(pk=sku_id, is_launched=True)
        except:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '库存商品编号无效'})
        # 处理
        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            redis_pl = redis_cli.pipeline()
            redis_pl.hdel('cart%d' % user.id, sku_id)
            redis_pl.srem('select%d' % user.id, sku_id)
            redis_pl.execute()
        else:
            # 读取cookie数据
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                cart_dict = {}
            else:
                cart_dict = item_mall_json.loads(cart_str)
                # 删除指定库存商品
                if sku_id in cart_dict:
                    del cart_dict[sku_id]
                # 写入cookie
                cart_str = item_mall_json.dumps(cart_dict)
                response.set_cookie('cart', cart_str, max_age=constants.CART_EXPIRES)
        return response

class CartSelectView(View):
    def put(self,request):
        #设置选中状态
        #接收
        param_dict = json.loads(request.body.decode())
        selected = param_dict.get('selected',True)
        # 验证
        if not isinstance(selected,bool):
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'选中状态不正确'})
        # 处理
        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok'})
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            # 修改
            if selected:
                #在hash中查询当前用户的所有库存商品
                sku_ids = redis_cli.hkeys('cart%d'%user.id)
                #加入set中（set自动去重）
                redis_cli.sadd('selected%d'%user.id,*sku_ids)
            else:
                redis_cli.delete('selected%d'%user.id)
        else:
            # 1.读取cookie中的购物车数据
            cart_str = request.COOKIES.get('cart')
            if cart_str is None:
                cart_dict = {}
            else:
                cart_dict = item_mall_json.loads(cart_str)
            # 2.遍历字典，修改选中属性
            for sku_id, cart in cart_dict.items():
                cart['selected'] = selected
            # 3.写cookie
            cart_str = item_mall_json.dumps(cart_dict)
            response.set_cookie('cart', cart_str, max_age=constants.CART_EXPIRES)

            # 响应
        return response

class CartSimpleView(View):
    #鼠标放在购物车上显示购物车数据
    def get(self,request):
        user = request.user
        #判断登陆
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')

            cart_dict = redis_cli.hgetall('cart%d' % user.id)

            # 将bytes转int

            cart_dict = {int(sku_id): int(count) for sku_id, count in cart_dict.items()}
        else:
            #未登录
            cart_str = request.COOKIES.get('cart')
            if cart_str is not None:
                cart_dict = item_mall_json.loads(cart_str)
                cart_dict = {sku_id:cart['count'] for sku_id,cart in cart_dict.items()}
            else:
                cart_dict ={}

        #查询库存商品对象
        skus = SKU.objects.filter(pk__in=cart_dict.keys(), is_launched=True)
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'count':cart_dict[sku.id]
            })
        return http.JsonResponse({

            'code': RETCODE.OK,

            'errmsg': 'ok',

            'cart_skus': sku_list

        })
