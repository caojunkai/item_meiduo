from item_mall.libs.yuntongxun.sms import CCP

from celery_tasks.main import app

@app.task(bind=True, name='send_sms', retry_backoff=3)
def send_sms(self, to, datas, tempid):

    try:

        # ccp = CCP()

        # ret = ccp.send_template_sms(to, datas, 1)

        print(datas[0])

    except Exception as e:

        self.retry(exc=e, max_retries=3)
