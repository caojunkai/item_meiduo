from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import Address
from django_redis import get_redis_connection
from goods.models import SKU
# Create your views here.



class SettlementView(LoginRequiredMixin,View):
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
    def get(self,request):
        user = request.user





