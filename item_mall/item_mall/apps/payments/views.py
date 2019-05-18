import os
from item_mall.settings import dev
from alipay import AliPay
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from orders.models import OrderInfo, OrderGoods
from django import http
import json
from item_mall.utils.response_code import RETCODE
from .models import Payment


# Create your views here.


class PaymentView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        user = request.user
        try:
            order = OrderInfo.objects.get(order_id=order_id, user_id=user.id)
        except:
            return http.HttpResponseForbidden('订单信息错误')
        alipay = AliPay(
            appid=dev.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(dev.BASE_DIR, "apps/payments/keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(dev.BASE_DIR, "apps/payments/keys/app_public_key.pem"),
            sign_type="RSA2",
            debug=dev.ALIPAY_DEBUG
        )
        # 生成登录支付宝连接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=dev.ALIPAY_RETURN_URL,
        )

        # 响应登录支付宝连接
        # 真实环境电脑网站支付网关：https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境电脑网站支付网关：https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = dev.ALIPAY_URL + "?" + order_string
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


class PaymentStatusView(View):
    def get(self, request):
        param_dict = request.GET.dict()
        print(param_dict)
        signature = param_dict.pop('sign')
        alipay = AliPay(
            appid=dev.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(dev.BASE_DIR, "apps/payments/keys/app_private_key.pem"),
            alipay_public_key_path=os.path.join(dev.BASE_DIR, "apps/payments/keys/app_public_key.pem"),
            sign_type="RSA2",
            debug=dev.ALIPAY_DEBUG
        )
        result = alipay.verify(param_dict, signature)
        order = OrderInfo.objects.get(pk = param_dict.get('out_trade_no'))
        print(order.order_id)
        # trade_id = param_dict.get('trade_no')
        # print(trade_id)
        try:
            if result:
                Payment.objects.create(
                    order=order,
                    trade_id=param_dict.get('trade_no')
                )

            # 修改订单状态

                OrderInfo.objects.filter(pk=param_dict.get('out_trade_no')).update(status=2)

                context = {
                    'alipay_id':param_dict.get('trade_no'),
                    'payment_amount':order.total_amount,
                    'order_id':order.order_id,
                }
                return render(request, 'pay_success.html', context)
            else:
                return http.JsonResponse({
                    'code':RETCODE.PARAMERR,
                    'errmsg':'支付失败，请重新支付'
                })

        except:
            context = {
                'alipay_id': param_dict.get('trade_no'),
                'payment_amount': order.total_amount,
                'order_id': order.order_id,
            }
            return render(request, 'pay_success.html', context)
