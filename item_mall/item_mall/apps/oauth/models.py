from django.db import models
from item_mall.utils.models import BaseModel
from users.models import User

# Create your models here.


class OAuthQQUser(BaseModel):
    user = models.ForeignKey(User)
    openid = models.CharField(max_length=50)
    class Meta:
        db_table = 'tb_oauth_qq'
