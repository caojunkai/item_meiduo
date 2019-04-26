from django.shortcuts import render, redirect

from django.views import View

from django import http

from django.contrib.auth import login,logout

import re

from .models import User

from item_mall.utils.response_code import RETCODE
from django.urls import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.
from django.views import View


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request, 'register.html')

    def post(self,request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        password2 = request.POST.get('cpwd')
        mobile = request.POST.get('phone')
        allow = request.POST.get('allow')
        # 判断参数是否齐全
        # 非空
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        # 用户名
        # 判断用户名是否是5-20个字符

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if User.objects.filter(username=username).count() > 0:
            return http.HttpResponseBadRequest('用户名已存在')
        # 密码
        # 判断密码是否是8-20个数字

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 判断两次密码是否一致
        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')
        # 手机号
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        if User.objects.filter(mobile=mobile).count() > 0:
            return http.HttpResponseBadRequest('手机号已存在')
        # 判断是否勾选用户协议
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')
        # try:
        #     User.objects.create_user(username=username, password=password, mobile=mobile)
        # except DatabaseError:
        #     return render(request, 'register.html', {'register_errmsg': '注册失败'})
        user = User.objects.create_user(username=username, password=password, mobile=mobile)


        # 保持状态
        login(request,user)
        url = reverse('users:index')
        # 响应注册结果
        response =  redirect(url)
        response.set_cookie('username',user.username,max_age=60 * 60 * 24 * 14)
        return response

class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页广告界面"""
        return render(request, 'index.html')



class UsernameCountView(View):
    def get(self,request,username):
        # 处理 查询有多少条相同记录
        count = User.objects.filter(username = username).count()
#         响应
        return http.JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'OK',
            'count':count
        })

class MobileCountView(View):
    def get(self,request,mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'OK',
            'count':count
        })
class LoginView(View):
    def get(self,request):
        return render(request,'login.html')
    def post(self,request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remembered = request.POST.get('remembered')
        next_url = request.GET.get('next','/')
        if not all([username,password]):
            return http.HttpResponseForbidden('缺少必要参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return  http.HttpResponseForbidden('请输入正确用户名或手机号')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        user = authenticate(username = username,password = password)
        if user is None:
            return render(request,'login.html',{'err_msg':'账户不对'})
        else:
            login(request, user)
        # 设置状态保持的周期
            if remembered != 'on':
                # 没有记住用户：浏览器会话结束就过期
                request.session.set_expiry(0)
            else:
                # 记住用户：None表示两周后过期
                request.session.set_expiry(None)

        # 响应登录结果
        #     url = reverse('users:index')

            response = redirect(next_url)
            response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 14)
            # 响应注册结果
            return response
class LogoutView(View):
    def get(self, request):

        # 删session

        logout(request)

        # 删cookie中的username

        response = redirect('/')

        response.delete_cookie('username')

        return response

class InfoView(LoginRequiredMixin, View):

    def get(self, request):

        # 判断是否登录

        # if request.user.is_authenticated:

        #     # 已登录

        #     return render(request, 'user_center_info.html')

        # else:

        #     # 未登录

        #     return redirect('/login/')
        return render(request, 'user_center_info.html')
