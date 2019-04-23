from django.shortcuts import render, redirect

from django.views import View

from django import http

from django.contrib.auth import login

import re

from .models import User

from item_mall.utils.response_code import RETCODE



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


        # 响应注册结果
        return redirect('/')

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


