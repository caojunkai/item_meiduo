#!/usr/bin/env python

# 第一行指定Python脚本解析器

# 3.添加Python脚本导包路径
import sys
sys.path.insert(0,'../')
# 4.设置Python脚本Django环境
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'item_mall.settings.dev'
import django
django.setup()



# 5.编写静态化详情页Python脚本代码
from celery_tasks.detail.tasks import generate_static_detail_html

from goods.models import SKU

if __name__ == '__main__':
    '''

        遍历商品表中的数据，生成静态页面

        '''
    skus = SKU.objects.filter(is_launched=True)
    for sku in skus:
        generate_static_detail_html(sku.id)
    print('ok')