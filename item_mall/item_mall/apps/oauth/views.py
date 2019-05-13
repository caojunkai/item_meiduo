from django.shortcuts import render,redirect

from django.views import View

from django import http

from QQLoginTool.QQtool import OAuthQQ

from django.conf import settings

from item_mall.utils.response_code import RETCODE
from .models import OAuthQQUser
from item_mall.utils import meiduo_signature
from . import contants
from users.models import User
from django.contrib.auth import login
from carts.utils import merge_cart_cookie_to_redis



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

            try:
                # 查询
                qquser = OAuthQQUser.objects.get(openid = openid)
            except:
                # 未绑定则定位到绑定页面
                token = meiduo_signature.dumps({'openid':openid},contants.OPENID_EXPIRES)
                context = {'token':token}
                return render(request,'oauth_callback.html',context)
            else:
                login(request,qquser.user)
                response = redirect(next_url)
                response.set_cookie('username',qquser.user.username,max_age=60*60*24*14)
                return response

        except:
            openid = '授权失败'

        return http.HttpResponse(openid)

    def post(self,request):
        mobile = request.POST.get('mobile')
        pwd = request.POST.get('pwd')
        sms_code_request = request.POST.get('sms_code')
        access_token = request.POST.get('access_token')
        next_url = request.GET.get('state')
        json = meiduo_signature.loadds(access_token,contants.OPENID_EXPIRES)
        if json is None:
            return http.HttpResponseBadRequest('授权无效，请重试')
        openid = json.get('openid')
        try:
            user = User.objects.get(mobile=mobile)
        except:
            user = User.objects.create_user(username = mobile,password = pwd,mobile = mobile)
        else:
            if not user.check_password(pwd):
                return http.HttpResponseBadRequest('密码错误')
        OAuthQQUser.objects.create(user = user,openid = openid)
        login(request,user)
        response = redirect(next_url)
        response = merge_cart_cookie_to_redis(request,response)
        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)
        return response


