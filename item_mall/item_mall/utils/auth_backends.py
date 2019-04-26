from django.contrib.auth.backends import ModelBackend
import re
from users.models import User


class ItemModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            if re.match('^1[3-9]\d{9}$', username):
                user = User.objects.get(mobile=username)
            else:
                user = User.objects.get(username=username)
        except:
            return
        else:
            if user.check_password(password):
                return user
            else:
                return None

