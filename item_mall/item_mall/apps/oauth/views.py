from django.shortcuts import render

from django.views import View

from django import http

from QQLoginTool.QQtool import OAuthQQ

from django.conf import settings

from item_mall.utils.response_code import RETCODE


# Create your views here.

class QQurlView(View):

    def get(self, request):

        # 生成QQ授权地址url

        next_url = request.GET.get('next', '/')

        # 创建工具对象，提供appid、appkey、回调地址

        oauthqq_tool = OAuthQQ(

            settings.QQ_CLIENT_ID,

            settings.QQ_CLIENT_SECRET,

            settings.QQ_REDIRECT_URI,

            next_url

        )
        # 调用方法生成授权地址(扫码页面)

        login_url = oauthqq_tool.get_qq_url()
        # 响应,返回扫码页面

        return http.JsonResponse({

            'code': RETCODE.OK,

            'errmsg': 'OK',

            'login_url': login_url

        })
class QQopenidView(View):
    def get(self,request):
        # 获取授权用户的唯一标识openid

        # 接收code

        code = request.GET.get('code')

        next_url = request.GET.get('state', '/')
        # 创建工具对象，提供appid、appkey、回调地址
        oauthqq_tool = OAuthQQ(
            settings.QQ_CLIENT_ID,
            settings.QQ_CLIENT_SECRET,
            settings.QQ_REDIRECT_URI,
            next_url
        )
        try:
            # 根据code获取token
            token = oauthqq_tool.get_access_token(code)

            # 根据token获取openid
            openid = oauthqq_tool.get_open_id(token)
        except:
            openid = '授权失败'

        return http.HttpResponse(openid)

