from django.shortcuts import render, redirect

from django.views import View

from django import http

from django.contrib.auth import login,logout

import re

from .models import User,Address

from item_mall.utils.response_code import RETCODE
from django.urls import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from item_mall.utils import meiduo_signature
from . import contants
from django.conf import settings
from celery_tasks.mail.tasks import send_user_email
from django_redis import get_redis_connection



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

        #提供个人信息
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
        }
        return render(request, 'user_center_info.html',context)

class EmailView(LoginRequiredMixin,View):

    def put(self,request):
        "实现添加邮箱逻辑"
        dict1 = json.loads(request.body.decode())
        email = dict1.get('email')
        if not all([email]):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '没有邮箱参数'
            })
        if not re.match('^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '邮箱格式错误'
        })
        #修改属性
        user = request.user
        user.email = email
        user.save()

        token = meiduo_signature.dumps({'user_id': user.id},contants.EMAIL_EXPIRES)
        verify_url = settings.EMAIL_VERIFY_URL + '?token=%s' % token
        send_user_email.delay(email, verify_url)
        # 响应
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'OK'
        })

class EmailVerifyView(View):
    def get(self,request):
        # 接收
        token = request.GET.get('token')
        #验证
        dict1 = meiduo_signature.loadds(token,contants.EMAIL_EXPIRES)
        if dict1 is None:
            return http.HttpResponseBadRequest('激活失败，请从新发送邮件')
        # 接收 请求用户的的id
        user_id = dict1.get('user_id')
        #处理
        try:
            user = User.objects.get(pk = user_id)
        except:
            return http.HttpResponseBadRequest('激活用户无效')
        else:
            user.email_active = True
            user.save()
        return redirect('/info/')

class AddressView(LoginRequiredMixin, View):

    def get(self, request):
        #接受用户名
        Login_user = request.user
        address = Address.objects.filter(user = Login_user,is_delete=False)
        data_list = []
        for i in address:
            data_list.append(i.to_dict())
            # data_list.append(Address.to_dict(i))

        context = {
            'addresses':data_list,
            'user':Login_user
        }

        return render(request, 'user_center_site.html',context)

#添加类
class AddressCreateView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        count = Address.objects.filter(user =request.user).count()
        if count > 20:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '超过地址数量上限'})


        json_dict = json.loads(request.body.decode())

        receiver = json_dict.get('receiver')

        province_id = json_dict.get('province_id')

        city_id = json_dict.get('city_id')

        district_id = json_dict.get('district_id')

        place = json_dict.get('place')

        mobile = json_dict.get('mobile')

        tel = json_dict.get('tel')

        email = json_dict.get('email')
        # 验证
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '参数不完整'
            })
        # 格式验证
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '手机号格式错误'
            })
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({
                    'code': RETCODE.PARAMERR,
                    'errmsg': '固定电话格式错误'
                })
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({
                    'code': RETCODE.PARAMERR,
                    'errmsg': '邮箱格式错误'
                })
        address = Address.objects.create(
            user=user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            detail=place,
            mobile=mobile,
            phone=tel,
            email=email
        )
        # 判断当前用户有没有默认地址，没有设置此地址为默认
        if user.default_address is None:
            user.default_address = address
            user.save()
        return http.JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'ok',
            'address':address.to_dict()
        })

# class AddressCreateView(LoginRequiredMixin, View):
#     def post(self, request):
#
#         # 添加收货地址
#
#         user = request.user
#
#         # 接收
#
#         '''
#
#         request.GET===>查询参数
#
#         request.POST===><form method='post'></form>
#
#         request.body===>ajax请求中的json数据
#
#         '''
#
#         dict1 = json.loads(request.body.decode())
#
#         # title = dict1.get('title')
#
#         receiver = dict1.get('receiver')
#
#         province_id = dict1.get('province_id')
#
#         city_id = dict1.get('city_id')
#
#         district_id = dict1.get('district_id')
#
#         place = dict1.get('place')
#
#         mobile = dict1.get('mobile')
#
#         tel = dict1.get('tel')
#
#         email = dict1.get('email')
#
#         # 验证
#         if not all([receiver, province_id, city_id, district_id, place, mobile]):
#             return http.JsonResponse({
#                 'code': RETCODE.PARAMERR,
#                 'errmsg': '参数不完整'
#             })
#         # 格式验证
#         if not re.match(r'^1[3-9]\d{9}$', mobile):
#             return http.JsonResponse({
#                 'code': RETCODE.PARAMERR,
#                 'errmsg': '手机号格式错误'
#             })
#         if tel:
#             if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
#                 return http.JsonResponse({
#                     'code': RETCODE.PARAMERR,
#                     'errmsg': '固定电话格式错误'
#                 })
#         if email:
#             if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
#                 return http.JsonResponse({
#                     'code': RETCODE.PARAMERR,
#                     'errmsg': '邮箱格式错误'
#                 })
#
#         # 处理：添加，创建对象***.objects.create()
#         address = Address.objects.create(
#             user=user,
#             title=receiver,
#             receiver=receiver,
#             province_id=province_id,
#             city_id=city_id,
#             district_id=district_id,
#             detail=place,
#             mobile=mobile,
#             phone=tel,
#             email=email
#         )
#         # 判断当前用户是否有默认地址，如果没有则设置为当前地址
#         if user.default_address is None:
#             user.default_address = address
#             user.save()
#
#         # 响应
#         return http.JsonResponse({
#             'code': RETCODE.OK,
#             'errmsg': 'ok',
#             'address': address.to_dict()
#         })



#修改类
class AddressUpdateView(LoginRequiredMixin,View):
    def put(self, request,address_id):
        # 接收
        user = request.user

        json_dict = json.loads(request.body.decode())

        receiver = json_dict.get('receiver')

        province_id = json_dict.get('province_id')

        city_id = json_dict.get('city_id')

        district_id = json_dict.get('district_id')

        place = json_dict.get('place')

        mobile = json_dict.get('mobile')

        tel = json_dict.get('tel')

        email = json_dict.get('email')
        # 验证
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '参数不完整'
            })
        # 格式验证
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '手机号格式错误'
            })
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({
                    'code': RETCODE.PARAMERR,
                    'errmsg': '固定电话格式错误'
                })
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({
                    'code': RETCODE.PARAMERR,
                    'errmsg': '邮箱格式错误'
                })
        try:
            address = Address.objects.get(PK = address_id,user=user,is_delete=False)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '收货地址编号错误'
            })
        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.detail = place
        address.mobile = mobile
        address.phone = tel
        address.email = email
        address.save()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
            'address': address.to_dict()
        })
    def delete(self,request,address_id):
        # 接收
        user = request.user
        try:
            address = Address.objects.get(pk = address_id,user = user,is_delete=False)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '收货地址编号错误'
            })
        address.is_delete = True
        address.save()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
        })
class AddressDefaultView(LoginRequiredMixin,View):
    def put(self,request,address_id):
        user = request.user
        user.default_address_id = address_id
        user.save()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',

        })

class AddressTitleView(LoginRequiredMixin,View):
    def put(self,request,address_id):
        json_dict = json.load(request.body.decode())
        title = json_dict.get('title')
        if not all ([title]):
            return http.JsonResponse({
                'code':RETCODE.PARAMERR,
                'errmsg':'标题不能为空'

            })
        try:
            address = Address.objects.get(pk = address_id,user = request.user,is_delete=False)
        except:
            return http.JsonResponse({
                'code': RETCODE.PARAMERR,
                'errmsg': '收货地址编号错误'
            })
        address.title = title
        address.save()
        return http.JsonResponse({
            'code': RETCODE.OK,
            'errmsg': 'ok',
        })
class PasswordView(LoginRequiredMixin,View):
    def get(self,request):
        return render(request,'user_center_pass.html')
    def post(self,request):
        old_pwd = request.POST.get('old_pwd')
        new_pwd = request.POST.get('new_pwd')
        new_cpwd = request.POST.get('new_cpwd')
        user = request.user

        if not all([old_pwd,new_pwd,new_cpwd]):
            return http.HttpResponseBadRequest('参数不够')
        if not user.check_password(old_pwd):
            return http.HttpResponseBadRequest('原密码错误')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseBadRequest('密码格式不对')
        if new_pwd != new_cpwd:
            return http.HttpResponseBadRequest('两次密码不一致')
        user.set_password(new_pwd)
        user.save()
        return render(request, 'user_center_pass.html')

