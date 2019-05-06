from django.db import models
from django.contrib.auth.models import AbstractUser
from item_mall.utils.models import BaseModel
from areas.models import Area
# Create your models here.




# Create your models here.


class User(AbstractUser):
    """自定义用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')
    # 默认收货地址
    default_address = models.ForeignKey('Address', related_name='users', null=True)

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

class Address(BaseModel):

    # 用户

    user = models.ForeignKey(User, related_name='addresses')

    # 标题

    title = models.CharField(max_length=10)

    # 收件人

    receiver = models.CharField(max_length=10)

    # 省

    province = models.ForeignKey(Area, related_name='provinces')

    # 市

    city = models.ForeignKey(Area, related_name='cities')

    # 区县

    district = models.ForeignKey(Area, related_name='districts')

    # 详细地址

    detail = models.CharField(max_length=50)

    # 收件人手机号

    mobile = models.CharField(max_length=11)

    # 电话

    phone = models.CharField(max_length=20)

    # 邮箱

    email = models.CharField(max_length=50)

    # 逻辑删除

    is_delete = models.BooleanField(default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'receiver': self.receiver,
            'province_id': self.province_id,
            'province': self.province.name,
            'city_id': self.city_id,
            'city': self.city.name,
            'district_id': self.district_id,
            'district': self.district.name,
            'place': self.detail,
            'mobile': self.mobile,
            'tel': self.phone,
            'email': self.email
        }
