from django.shortcuts import render

from django.views import View

from item_mall.libs.captcha.captcha import captcha

from django_redis import get_redis_connection

from django import http

from . import constants


# Create your views here.
class ImageCodeView(View):


    def get(self,request,uuid):
        text,code,image = captcha.generate_captcha()
        redis_cli = get_redis_connection('verify_code')
        redis_cli.setex(uuid, constants.IMAGE_CODE_EXPIRES, code)
        return http.HttpResponse(image, content_type='imgae/png')




