from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import Address
from django_redis import get_redis_connection
from goods.models import SKU
import json
from django import http
from item_mall.utils.response_code import RETCODE
import datetime
from .models import OrderInfo,OrderGoods
# Create your views here.



class SettlementView(LoginRequiredMixin,View):
    #提交订单页面展示
    def get(self,request):
        user = request.user
        # 查询收货地址
        addresses = Address.objects.filter(is_delete=False,user=user.id)
        #查询默认收货地址id
        default_address_id = user.default_address_id
        # 查询购物车中选中的商品，当前视图需要登录后才能访问，只通过redis获取购物车数据
        redis_cli = get_redis_connection('carts')
        #hash
        cart_dict = redis_cli.hgetall('cart%d'%user.id)
        cart_dict = {int(sku_id):int(count) for sku_id,count in cart_dict.items()}
        #set
        selected_list = redis_cli.smembers('selected%d'%user.id)
        selected_list = [int(sku_id)for sku_id in selected_list]
        # 查询库存商品
        skus = SKU.objects.filter(pk__in = selected_list,is_launched=True)
        # 转格式
        sku_list = []
        total_count = 0
        total_money = 0
        freight = 10 # 运费
        for sku in skus:
            #总数量
            total_count=+cart_dict[sku.id]
            total_miney = sku.price*cart_dict[sku.id]
            total_money += total_miney
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'price':sku.price,
                'count':cart_dict[sku.id],
                'total_amount':total_miney
            })
        pay_money = total_money + freight
        context = {
            'addresses':addresses,
            'default_address_id':default_address_id,
            'sku_list':sku_list,
            'total_count':total_count,
            'total_money':total_money,
            'freight': freight,
            'pay_money':pay_money

        }
        return render(request,'place_order.html',context)

class OrderCommitView(LoginRequiredMixin,View):
    #创建订单
    def post(self,request):
        '''

                创建订单对象、订单商品对象

                参数 address_id：收货地址编号

                参数 pay_method：支付方式编号

                '''

        # 接收
        user = request.user
        param_dict = json.loads(request.body.decode())
        address_id = param_dict.get('address_id')
        pay_method = param_dict.get('pay_method')
        #验证
        if not all([address_id,pay_method]):
            return http.JsonResponse({
                'code':RETCODE.PARAMERR,
                'errmsg':'参数不够'
            })
        try:
            address = Address.objects.get(pk = address_id,user_id=user.id)
        except:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'收货地址无效'})
        # 支付方式，当前只允许[1,2]
        if pay_method not in [1, 2]:
            return http.JsonResponse({'code':RETCODE.PARAMERR,'errmsg':'付款方式不对'})
        #从购物车中查询选中商品
        redis_cli = get_redis_connection('carts')
        cart_dict = redis_cli.hgetall('cart%d'%user.id)
        cart_dict = {int(sku_id):int(count) for sku_id,count in cart_dict.items()}
        selected_list = redis_cli.smembers('selected%d'%user.id)
        selected_list = [int(sku_id)for sku_id in selected_list]
        #创建订单对象
        now = datetime.now()
        tatal_count = 0 #数量
        tatal_amount = 0 #单价
        if pay_method ==1:  #货到付款
            status = 2
        else:
            status = 1
        order_id = '%s%09d'%(now.strftime('%Y%m%d%H%M%S'),user.id)
        order = OrderInfo.objects.create(
            order_id=order_id,
            user_id=user.id,
            address_id=address_id,
            total_count=tatal_count,
            total_amount=tatal_amount,
            freight=10,
            pay_method=pay_method,
            status=status
        )
        # 查询库存商品，遍历
        skus = SKU.objects.filter(pk__in = selected_list,is_launched=True)
        for sku in skus:
            count = cart_dict[sku.id]
            # 3.1判断库存是否足够，如果不足则返回提示，如果库存足够，则继续
            if sku.stock < count:
                return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
            # 修改商品库存，销量
            sku.stock -=count
            sku.sales+=count
            sku.save()
            # 创建订单商品
            order_goods = OrderGoods.objects.create(
                order_id=order_id,
                sku_id=sku.id,
                count=count,
                price=sku.price
            )





