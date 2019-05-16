import time
from django.shortcuts import render
from .models import ContentCategory
from item_mall.utils.meiduo_category import get_categories
import os
from django.conf import settings



def generate_static_index_html():
    print('%s: generate_static_index_html' % time.ctime())
    #获取商品频道和分类
    categories = get_categories()
    #广告内容
    contents={}
    content_categories = ContentCategory.objects.all()
    for cat  in content_categories:
        contents[cat.key] = cat.content_set.filter(status = True).order_by('sequence')


    #渲染模板
    context = {
        'categories':categories,
        'contents':contents
    }
    response = render(None,'index.html',context)
    html_str = response.content.decode()
    #写入文件中
    file_path = os.path.join(settings.BASE_DIR,'static/index.html')
    with open(file_path,'w') as f:
        f.write(html_str)














