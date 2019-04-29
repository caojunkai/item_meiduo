from celery import Celery

import os

# 读取django项目的配置，加入环境变量中

os.environ["DJANGO_SETTINGS_MODULE"] = "item_mall.settings.dev"

# 创建主对象

app = Celery('meiduo')

# 读取配置：指定消息队列，当前使用redis

app.config_from_object('celery_tasks.config')

# 自动识别

app.autodiscover_tasks([

    'celery_tasks.sms',
    'celery_tasks.mail',

])













