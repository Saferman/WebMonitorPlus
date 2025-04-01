from django.db import models


class SystemMailSetting(models.Model):
    mail_server = models.CharField(max_length=32,
                                   null=False,
                                   default='localhost',
                                   verbose_name='邮箱服务器')
    mail_port = models.IntegerField(null=False, default=25, verbose_name='端口')
    mail_username = models.CharField(max_length=64,
                                     null=False,
                                     default='默认用户名',
                                     verbose_name='用户名')
    mail_sender = models.CharField(max_length=64,
                                   null=False,
                                   default='默认用户名@mail.com',
                                   verbose_name='发件人')
    mail_password = models.CharField(max_length=64,
                                     null=False,
                                     default='默认密码',
                                     verbose_name='密码')

    class Meta:
        verbose_name = "系统邮箱"
        verbose_name_plural = "系统邮箱"

    def __str__(self):
        return self.mail_server


class PushoverSetting(models.Model):
    api_token = models.CharField(max_length=100,
                                 null=False,
                                 verbose_name='Pushover API Token')

    class Meta:
        verbose_name = "Pushover 设置"
        verbose_name_plural = "Pushover 设置"

    def __str__(self):
        return 'Pushover ' + self.api_token


class Notification(models.Model):
    type_choice = ((0, '邮箱'), (1, '微信'), (2, 'pushover'), (3, 'Bark'),
                   (4, '自定义通知'), (5, 'Slack'), (6, 'Telegram'))
    name = models.CharField(max_length=32,
                            null=False,
                            verbose_name='通知方式名称',
                            unique=True,
                            default='默认名称')
    type = models.IntegerField(null=False,
                               choices=type_choice,
                               default='邮箱',
                               verbose_name='通知方式类型')
    content = models.CharField(max_length=512,
                               null=False,
                               verbose_name='邮箱地址 / Server 酱 SCKEY / \
            Pushover User Key / Bark key / 自定义网址 / Slack channel / Telegram chat_id'
                               )

    class Meta:
        verbose_name = "通知方式"
        verbose_name_plural = "通知方式"

    def __str__(self):
        return self.name


class Log(models.Model):
    class Meta:
        verbose_name = "日志查看"
        verbose_name_plural = "日志查看"


class SlackSetting(models.Model):
    token = models.CharField(max_length=100,
                             null=False,
                             verbose_name='Slack OAuth Access Token')

    class Meta:
        verbose_name = "Slack 设置"
        verbose_name_plural = "Slack 设置"

    def __str__(self):
        return 'Slack ' + self.token

class BarkSetting(models.Model):
    domain = models.CharField(max_length=100,
                             null=False,
                             verbose_name='Bark server url',help_text='https://api.day.app或者http://8.210.22.195:8080，请注意不要/结尾')

    class Meta:
        verbose_name = "Bark 设置"
        verbose_name_plural = "Bark 设置"

    def __str__(self):
        return self.domain


class TelegramSetting(models.Model):
    token = models.CharField(max_length=100,
                             null=False,
                             verbose_name='Telegram Bot Token')

    class Meta:
        verbose_name = "Telegram Bot 设置"
        verbose_name_plural = "Telegram Bot 设置"

    def __str__(self):
        return 'Telegram Bot ' + self.token
