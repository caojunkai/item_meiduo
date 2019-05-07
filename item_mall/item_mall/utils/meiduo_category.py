from goods.models import GoodsChannel,GoodsCategory

# 3级导航
def get_categories():
    # 查询所有频道 并排序
    channels = GoodsChannel.objects.order_by('group_id','sequence')


    # 遍历,转换成适合前端的数据结构
    catetories = {}
    for channel in channels:
        # 判断组是否存在
        if channel.group_id not  in catetories:

            # 创建catetories内的字典
            catetories[channel.group_id] ={
                'channels':[], # 一级分类列表
                'sub_cats':[]   # 二级分类列表
            }
        #一下全都是字典catetories内的
        #将 catetories内的字典 键赋值给channel_dict
        channel_dict = catetories[channel.group_id]
        #向字典的值（列表形式）添加数据
        channel_dict['channels'].append({
            'name':channel.category.name,
            'url':channel.url
        })


        '''
        循环创建的catetories

        categories={

            1:{

                'channels':[{手机},{相机},{数码}],

                'sub_cats':[]

            },

            2:{

                'channels':[{电脑},{办公}],

                'sub_cats':[]

            },

            3:{

                'channels':[],

                'sub_cats':[]

            }

        }

        '''
        # dicts = GoodsCategory.objects.order_by('parent_id')
        # dicts1 = {}
        #获取二级标题
        dicts = GoodsCategory.objects.filter(parent_id = channel.category)

        # print(dicts)
        for cat2 in dicts:
            # 获取三级标题列表
            dicts2 = GoodsCategory.objects.filter(parent_id=cat2.pk)
            # print(dicts2)
            channel_dict['sub_cats'].append({
                'name':cat2.name,
                'sub_cats': dicts2,
            })
        # # 1.6向二级分类中添加数据
        #
        # for cat2 in channel.category.subs.all():
        #     channel_dict['sub_cats'].append({
        #
        #         'name': cat2.name,
        #
        #         # 1.7添加三级分类
        #
        #         'sub_cats': cat2.subs.all()
        #
        #     })

    return catetories
