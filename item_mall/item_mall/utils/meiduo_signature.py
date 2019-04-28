from itsdangerous import TimedJSONWebSignatureSerializer as Encrypt
from django.conf import settings

# 加密
def dumps(json,expires):
    encrypt = Encrypt(settings.SECRET_KEY,expires)
    s1 = encrypt.dumps(json)
    return s1.decode()

#解密
def loadds(s1,expires):
    encrypt = Encrypt(settings.SECRET_KEY,expires)
    try:
        json = encrypt.loads(s1)
    except:
        return None
    return json

