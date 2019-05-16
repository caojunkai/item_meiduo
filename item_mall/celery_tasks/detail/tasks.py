from django.shortcuts import render
from item_mall.utils.meiduo_category import get_categories
from goods.models import SKU
from item_mall.utils.breadcrumb import get_breadcrumb
from django.conf import settings
import os
from celery_tasks.main import app


@app.task(name='generate_static_detail_html')
def generate_static_detail_html(sku_id):
    try:
        sku = SKU.objects.get(id=sku_id)
    except:
        return render(None, '404.html')
    # 三级分类
    category3 = sku.category
    # 频道分类
    categories = get_categories()
    # 面包屑导航
    breadcrumb = get_breadcrumb(category3)
    # 获取当前展示商品的规格信息
    sku_specs = sku.specs.order_by('spec_id')
    # 当前商品的规格选项添入列表
    sku_list = [info.option_id for info in sku_specs]
    # print('--', sku_list)

    # 获取标准商品表对象
    spu = sku.spu
    # 标准商品（spu)到库存商品(sku)到商品规格sku_specs(specs)信息
    skus = spu.sku_set.filter(is_launched=True)
    # 将每种商品的规格遍历出来 例如（13,20）（13,21）同为钻雕金  20 64g 21  128g
    sku_option_dict = {}
    for sku_info in skus:
        sku_info_options = sku_info.specs.order_by('spec_id')
        sku_info_option_list = [option_info.option_id for option_info in sku_info_options]
        # 将选项列表为键，库存商品编号为值
        # tuple将列表转成元祖  因为字典的键必须为不可修改
        sku_option_dict[tuple(sku_info_option_list)] = sku_info.id

    # 通过关系属性获取所有的规格
    specs = spu.specs.all()
    # print('--a', specs)
    specs_list = []
    # 转换数据格式
    # 遍历规格
    for index, spec in enumerate(specs):

        spec_dict = {
            'name': spec.name,
            'options': []
        }
        # 查询所有spec规格所有选项
        options = spec.options.all()
        # 将选项添加进列表
        for option in options:
            option_dict = {
                'name': option.value,
                'id': option.id
            }
            # 复制当前库存商品的选项
            sku_option_list_temp = sku_list[:]
            # print('===', sku_option_list_temp)
            # 当前选项是否选中
            if option.id in sku_list:
                option_dict['selected'] = True
            else:
                option_dict['selected'] = False

            # 为选项指定库存商品编号
            sku_option_list_temp[index] = option.id
            ti = tuple(sku_option_list_temp)
            # print(sku_option_list_temp)
            option_dict['sku_id'] = sku_option_dict.get(ti, 0)
            spec_dict['options'].append(option_dict)

            # 列表里有多个字典（spec_dict）
        specs_list.append(spec_dict)

    context = {
        'categories': categories,
        'breadcrumb': breadcrumb,
        'sku': sku,
        'spu': spu,
        'category_id': category3.id,
        'specs': specs_list
    }
    #获取页面字符
    response = render(None,'detail.html',context)
    html_str = response.content.decode()
    # 文件路径
    file_path = os.path.join(settings.BASE_DIR,'static/details/%d.html' % sku.id)
    print(file_path)
    with open(file_path, 'w') as f1:
        f1.write(html_str)