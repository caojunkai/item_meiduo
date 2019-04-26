import random

from django.shortcuts import render

from django.views import View

from item_mall.libs.captcha.captcha import captcha

from django_redis import get_redis_connection
from item_mall.utils.response_code import RETCODE

from django import http

from users.models import User
from . import constants
from item_mall.libs.yuntongxun.sms import CCP
from . import constants
from celery_tasks.sms.tasks import send_sms
# from item_mall.apps.users.models import User


# Create your views here.
class ImageCodeView(View):


    def get(self,request,uuid):
        text,code,image = captcha.generate_captcha()
        redis_cli = get_redis_connection('verify_code')
        redis_cli.setex(uuid, constants.IMAGE_CODE_EXPIRES, code)
        return http.HttpResponse(image, content_type='imgae/png')

class SmsCodeView(View):
    def get(self,request,mobile):
        # 接收用户填写的图形验证码文本
        image_code_request = request.GET.get('image_code')
        # 图形验证码的唯一编号
        uuid = request.GET.get('image_code_id')
        # 验证图形码是否正确
        redis_cli = get_redis_connection('verify_code')
        image_code_redis = redis_cli.get(uuid)
        if not image_code_redis:
            return http.JsonResponse({
                'code':RETCODE.PARAMERR,
                'errmsg':'图形验证码已过期'
            })
        # 用过一次就删
        redis_cli.delete(uuid)
       # 验证用户输入值是否正确    decode()把数据库中的数据（二进制）转化   upper:小写字符转化成大写的函数
        count = User.objects.filter(mobile=mobile).count()
        if count>0:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '手机号已注册'
            })
        if image_code_redis.decode()!= image_code_request.upper():
            return http.JsonResponse({
                'code':RETCODE.PARAMERR,
                'errmsg':'图形验证码错误'
            })
        if redis_cli.get('sms_flag_'+mobile):
            return http.JsonResponse({
                'code':RETCODE.PARAMERR,
                'errmsg':'已发过'
            })

        sms_code = '%06d' % random.randint(0,99999)
        # redis_cli.setex('sms_' + mobile, constants.SMS_CODE_EXPIRES, sms_code)
        # # 存储60s发送的标记
        # redis_cli.setex('sms_flag_' + mobile, constants.SMS_CODE_FLAG_EXPIRES, 1)
        # 使用pipeline，只与redis服务器交互一次，执行多条命令
        redis_pl = redis_cli.pipeline()
        redis_pl.setex('sms_' + mobile, constants.SMS_CODE_EXPIRES, sms_code)
        redis_pl.setex('sms_flag_' + mobile, constants.SMS_CODE_FLAG_EXPIRES, 1)
        redis_pl.execute()

        # 3.发短信
        # ccp = CCP()
        # ret = ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_EXPIRES / 60], 1)
        print(sms_code)
        send_sms.delay(mobile, [sms_code, constants.SMS_CODE_EXPIRES / 60], 1)

        # 响应
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': "OK"
        })