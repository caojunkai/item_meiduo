from django.shortcuts import render

from django.views import View

from .models import Area

from django import http

from item_mall.utils.response_code import RETCODE

from django.core.cache import cache

from . import constants


# Create your views here.



class AreaView(View):



    def get(self,request):
        #如果前端没有传入area_id，表示用户需要省份数据
# 如果前端传入了area_id，表示用户需要市或区数据
        area_id = request.GET.get('area_id')


        if not area_id:
            province_list = cache.get('province_list')

            #要是没有缓存
            if not province_list:

                try:
                    #查询省数据
                    province_model_list = Area.objects.filter(parent__isnull=True)

                    #序列化省级数据
                    province_list = []
                    for i in province_model_list:
                        province_list.append({'id':i.id,'name':i.name})
                except:
                    return  http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'省份数据错误'})

                cache.set('province_list', province_list, constants.AREA_CACHE_EXPIRES)

                # 相应省份数据
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            # 读缓存
            sub_data = cache.get('sub_area_'+ area_id)

            if not sub_data:

                try:
                    parent_model = Area.objects.get(id = area_id) #查询市或区的父级
                    sub_model_list = parent_model.subs.all()
                    # 序列化
                    sub_list = []
                    for i in sub_model_list:
                        sub_list.append({'id':i.id,'name':i.name})
                        sub_data = {
                            'id':parent_model.id,  #父级PK
                            'name':parent_model.name,
                            'subs':sub_list   #父级的子集
                        }
                except:
                    return http.JsonResponse({'code':RETCODE.DBERR,'errmsg':'市区数据错误'})

                    # 储存市或区缓存数据
                cache.set('sub_area_' + area_id, sub_data, constants.AREA_CACHE_EXPIRES)

            return http.JsonResponse({'code':RETCODE.OK,'errmsg':'OK','sub_data':sub_data})














