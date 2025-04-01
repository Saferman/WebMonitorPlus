import json
import logging
import re
import requests
import traceback


from setting.models import BarkSetting
from task.utils.notification.notification import Notification
import urllib.parse

logger = logging.getLogger('main')


def getUrlQuery(content):
    """
    Extract the first URL in the content with format of '?url=URL', return '' if none URL found.
    """
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    urls = re.findall(regex, content)
    if len(urls):
        url = [x[0] for x in urls][0]
        url_query = f'?url={urllib.parse.quote_plus(url)}'
        return url_query
    return ''


class BarkNotification(Notification):
    def __init__(self):
        try:
            setting = BarkSetting.objects.first()
        except Exception:
            logger.error('没有设置 Bark server url，无法发送通知')
            logger.error(traceback.format_exc())
            raise Exception('没有设置 Bark server url，无法发送通知')

        self.domain = setting.domain

    def send(self, to, header, content):
        """to是Bark Key也就是device key,header是任务名字，content是任务内容"""
        if to == '默认':
            logger.error('没有设置Bark KEY，无法发送Bark通知')
            raise Exception('没有设置Bark KEY，无法发送Bark通知')
        
        try:
            logger.info(f'Python脚本任务的通知内容：\n发送Bark通知的URL（结尾不能是/): {self.domain}\nDevice Key: {to}\nHeader（也是通知标题）: {header}\nContent（通知内容也是Python脚本执行结果）: {content}\n'+"-"*20)
            response = requests.post(
                url="{}/push".format(self.domain), #//push都会报错
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                },
                data=json.dumps({
                    "body": content,
                    "device_key": to,
                    "title": header,
                    "sound": "minuet",
                    "badge": 1,
                    # "icon": "https://day.app/assets/images/avatar.jpg",
                    "group": "test",
                })
            )
            if response.status_code != 200:
                raise Exception(response.text)

        except requests.exceptions.RequestException:
            raise Exception('Bark HTTP Request failed')

