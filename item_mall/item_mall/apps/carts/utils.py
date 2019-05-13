from item_mall.utils import item_mall_json
from django_redis import get_redis_connection



def merge_cart_cookie_to_redis(request,user,response):
    #登陆后合并数据库
    #获取cookie
    user = request.user
    cookie_cart_str = request.COOKIES.get('cart')
    if cookie_cart_str is None:
        return response
    cookie_cart_dict = item_mall_json.loads(cookie_cart_str)
#同步数据
    new_cart_dict = []
    new_selectes_add = []
    new_selectes_delete = []
    for sku_id,cart in cookie_cart_dict.items():
        new_cart_dict.append(sku_id)
        new_cart_dict.append(cart['count'])
        if cart['selected']:
            new_selectes_add.append(sku_id)
        else:
            new_selectes_delete.append(sku_id)
    redis_cli = get_redis_connection('carts')
    redis_pl = redis_cli.pipeline()

    redis_pl.hmset('cart%d'%user.id,new_cart_dict)
    if new_selectes_add:
        redis_pl.sadd('selected%d'%user.id,*new_selectes_add)
    else:
        redis_pl.srem('selected%d' % user.id, *new_selectes_delete)
    redis_pl.execute()
    response.delete_cookie('cart')
    return response
