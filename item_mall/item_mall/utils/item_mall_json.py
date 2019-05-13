import pickle
import base64


def dumps(dict1):

# 将字典转换成字符串

# 1.转字节
    dict_bytes = pickle.dumps(dict1)
    #2 加密
    str_bytes = base64.b64encode(dict_bytes)
    #转字符
    return str_bytes.decode()

#将字符串转成字典
def loads(str1):
    #转字符
    str_bytes = str1.encode()
    #解密
    dict_bytes = base64.b64decode(str_bytes)
    #转字典
    return pickle.loads(dict_bytes)
