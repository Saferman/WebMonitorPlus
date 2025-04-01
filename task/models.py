import logging
from datetime import datetime

from django.core.validators import MinValueValidator, URLValidator
from django.db import models

from setting.models import Notification

logger = logging.getLogger('main')

# def check_url(url):
#     try:
#         requests.get(url, timeout=10)
#     except Exception as e:
#         raise ValidationError({'url': e})

# def check_selector(selector_type, selector, url, is_chrome, headers):
#     try:
#         if is_chrome == 0:
#             selector_handler = new_handler('request')
#         else:
#             selector_handler = new_handler('phantomjs')

#         if selector_type == 0:
#             selector_handler.get_by_xpath(url, selector, headers)
#         elif selector_type == 1:
#             selector_handler.get_by_css(url, selector, headers)
#         elif selector_type == 2:
#             selector_handler.get_by_json(url, selector, headers)
#         else:
#             raise Exception('无效选择器')
#     except Exception as e:
#         raise ValidationError({'selector': e})


class Content(models.Model):
    task_id = models.IntegerField(null=False)
    content = models.CharField(max_length=512, null=False)
    task_type = models.CharField(max_length=32, null=False, default='html')


class TaskStatus(models.Model):
    task_id = models.IntegerField(null=False, verbose_name='任务ID')
    task_name = models.CharField(max_length=100,
                                 null=False,
                                 verbose_name='任务名称')
    last_run = models.DateTimeField(auto_now=True, verbose_name='上次运行时间')
    last_status = models.CharField(max_length=100,
                                   null=False,
                                   default='创建任务成功',
                                   verbose_name='上次运行结果')

    status_choices = ((0, 'run'), (1, 'stop'))

    task_status = models.IntegerField(null=False,
                                      default=0,
                                      verbose_name='任务状态',
                                      choices=status_choices)
    task_type = models.CharField(max_length=100,
                                 null=False,
                                 default='html',
                                 verbose_name='任务类型')

    class Meta:
        verbose_name = "任务状态"
        verbose_name_plural = "任务状态"

    def __str__(self):
        return self.task_name

    def save(self, *args, **kwargs):
        from task.utils.scheduler import add_job, remove_job

        super(TaskStatus, self).save(*args, **kwargs)
        task_id = self.task_id

        if self.task_status == 0:
            if self.last_status != '更新任务成功':
                if self.task_type == 'html':
                    task = PageMonitorTask.objects.get(id=task_id)
                    add_job(task_id, task.frequency)
                elif self.task_type == 'rss':
                    rss_task = RSSTask.objects.get(id=task_id)
                    add_job(task_id, rss_task.frequency, 'rss')
        else:
            if self.task_type == 'html':
                remove_job(task_id)
            elif self.task_type == 'rss':
                remove_job(task_id, 'rss')

    def short_last_status(self):
        if len(str(self.last_status)) > 100:
            return '{}......'.format(str(self.last_status)[:100])
        else:
            return str(self.last_status)

    short_last_status.allow_tags = True
    short_last_status.short_description = '上次运行结果'


class PageMonitorTask(models.Model):
    name = models.CharField(max_length=100, verbose_name='任务名称', null=False)
    url = models.CharField(max_length=1000,
                           verbose_name='监控网址',
                           null=False,
                           validators=[URLValidator()])

    selector_choices = (
        (0, 'Xpath'),
        (1, 'Css selector'),
        (2, 'JsonPath'),
    )

    selector_type = models.IntegerField(verbose_name='元素选择器类型',
                                        null=False,
                                        default='Xpath',
                                        choices=selector_choices)
    selector = models.TextField(verbose_name='元素选择器',
                                blank=False,
                                help_text='一行一个元素选择器，每一行的格式为：选择器名称{选择器内容}，\
            例如：title{//*[@id="id3"]/h3/text()}。其中 url 为系统保留选择器名称，请不要使用且无法被覆盖')
    template = models.TextField(
        verbose_name='消息体模板',
        blank=True,
        help_text='可为空，自定义发送的通知内容格式，按照选择器名称进行替换，具体示例见文档')
    is_chrome_choices = ((0, 'no'), (1, 'yes'))
    is_chrome = models.IntegerField(null=False,
                                    default='no',
                                    verbose_name='是否使用无头浏览器',
                                    choices=is_chrome_choices)
    frequency = models.FloatField(null=False,
                                  default=5,
                                  verbose_name='频率(分钟)',
                                  validators=[MinValueValidator(0)])
    create_time = models.DateTimeField(null=False,
                                       auto_now_add=True,
                                       verbose_name='创建时间')

    notification = models.ManyToManyField(Notification,
                                          blank=False,
                                          verbose_name='通知方式')

    regular_expression = models.CharField(max_length=500,
                                          verbose_name='正则表达式',
                                          blank=True,
                                          help_text='使用正则表达式进一步提取信息，可以留空')
    rule = models.CharField(max_length=500,
                            verbose_name='监控规则',
                            blank=True,
                            help_text='规则写法参考文档，留空则只简单监控内容变化')
    headers = models.TextField(verbose_name='自定义请求头',
                               blank=True,
                               help_text='自定义请求头，如可以设置cookie获取登录后才能查看的页面')

    class Meta:
        verbose_name = "网页监控"
        verbose_name_plural = "网页监控管理"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from task.utils.scheduler import add_job

        # 新建
        if not self.pk:
            super(PageMonitorTask, self).save(*args, **kwargs)
            id = self.pk

            add_job(id, self.frequency)

            task_status = TaskStatus(task_name=self.name, task_id=id)
            task_status.save()
        else:
            super(PageMonitorTask, self).save(*args, **kwargs)
            id = self.pk

            task_status = TaskStatus.objects.get(task_id=id, task_type='html')
            task_status.task_name = self.name
            task_status.last_status = '更新任务成功'
            task_status.last_run = datetime.now()
            task_status.task_status = 0
            task_status.save()

            add_job(id, self.frequency)
            logger.info('task_{}更新'.format(id))

    def delete(self, *args, **kwargs):
        from task.utils.scheduler import remove_job

        id = self.pk
        remove_job(id)

        TaskStatus.objects.filter(task_id=id, task_type='html').delete()
        Content.objects.filter(task_id=id, task_type='html').delete()

        logger.info('task_{}删除'.format(id))

        super(PageMonitorTask, self).delete(*args, **kwargs)


class RSSTask(models.Model):
    name = models.CharField(max_length=32, null=False, verbose_name='任务名称')
    url = models.CharField(max_length=1000,
                           null=False,
                           verbose_name='RSS地址',
                           validators=[URLValidator()])
    frequency = models.FloatField(null=False,
                                  default=5,
                                  verbose_name='频率(分钟)',
                                  validators=[MinValueValidator(0)])
    create_time = models.DateTimeField(null=False,
                                       auto_now_add=True,
                                       verbose_name='创建时间')

    notification = models.ManyToManyField(Notification,
                                          blank=False,
                                          verbose_name='通知方式')

    class Meta:
        verbose_name = "RSS监控"
        verbose_name_plural = "RSS监控管理"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from task.utils.scheduler import add_job

        # 新建
        if not self.pk:
            super(RSSTask, self).save(*args, **kwargs)
            id = self.pk

            add_job(id, self.frequency, 'rss')
            task_status = TaskStatus(task_name=self.name,
                                     task_id=id,
                                     task_type='rss')
            task_status.save()
        else:
            super(RSSTask, self).save(*args, **kwargs)

            id = self.pk
            task_status = TaskStatus.objects.get(task_id=id, task_type='rss')
            task_status.task_name = self.name
            task_status.last_status = '更新任务成功'
            task_status.last_run = datetime.now()
            task_status.task_status = 0
            task_status.save()

            add_job(id, self.frequency, 'rss')
            logger.info('task_RSS{}更新'.format(id))

    def delete(self, *args, **kwargs):
        from task.utils.scheduler import remove_job

        id = self.pk
        remove_job(id, 'rss')

        TaskStatus.objects.filter(task_id=id, task_type='rss').delete()
        Content.objects.filter(task_id=id, task_type='rss').delete()

        logger.info('task_RSS{}删除'.format(id))

        super(RSSTask, self).delete(*args, **kwargs)


class PythonScriptTask(models.Model):
    name = models.CharField(max_length=100, verbose_name='任务名称', null=False)
    script = models.TextField(verbose_name='Python脚本代码', null=False, 
                            help_text='请输入要执行的Python代码，目前只支持python3.8版本的，注意：\n'
                                    '1. result: 用于存储需要发送给用户消息，一定要设置为脚本的全局变量，且是字符串类型\n'
                                    '2. 请自行确保docker环境已经按照了模块，可以联系管理员添加requirements.txt\n'
                                    '3. result 为空字符串时，不发送消息\n'
                                    '4. 请注意if __name__ == "__main__"的内容是无法执行的'
                                    )
    
    description = models.TextField(verbose_name='脚本描述', null=False, 
                            help_text='简单描述一下脚本任务，方便管理的时候知道这个任务是做什么的'
                                    )

    # 执行频率
    frequency = models.FloatField(null=False, default=5, 
                                verbose_name='执行频率(分钟)', 
                                validators=[MinValueValidator(0)],help_text='可以小数会折算成秒，一个小时输入：60，一天输入：1440')
    
    # 时间记录
    create_time = models.DateTimeField(null=False, auto_now_add=True, 
                                     verbose_name='创建时间')

    # 执行条件
    is_enabled = models.BooleanField(default=True, verbose_name='是否启用')

    # 是否创建和更新时候立刻执行
    is_run_now = models.BooleanField(default=False, verbose_name='是否立刻执行',
                                     help_text='如果为True，则创建和更新任务时立刻执行')
    # 超时时间
    timeout = models.IntegerField(null=False, default=300, 
                                verbose_name='超时时间(秒)', 
                                validators=[MinValueValidator(0)])

    # 是否只在和上一次消息不一样的时候才发送
    no_repeat = models.BooleanField(default=True, verbose_name='是否去重',help_text='如果为True，则只有在和上一次消息不一样的时候才发送')

    # 通知设置
    notification = models.ManyToManyField(Notification, blank=False, 
                                        verbose_name='通知方式')
    
    # # 执行结果处理
    # success_condition = models.TextField(blank=True, verbose_name='成功条件', 
    #                                    help_text='Python表达式，用于判断脚本是否执行成功。例如：\n'
    #                                            'result.get("status") == "success"\n'
    #                                            '如果不设置，则脚本正常执行完成即视为成功')
    


    class Meta:
        verbose_name = "Python脚本任务"
        verbose_name_plural = "Python脚本任务管理"


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from task.utils.scheduler import add_job, remove_job
        
        # 新建任务
        if not self.pk:
            super(PythonScriptTask, self).save(*args, **kwargs)
            id = self.pk
            
            # 创建任务状态
            task_status = TaskStatus(
                task_name=self.name,
                task_id=id,
                task_type='python'
            )
            task_status.save()
            
            # 添加到调度器
            if self.is_enabled:
                add_job(id, self.frequency, 'python',self.is_run_now)
        
        # 更新任务
        else:
            super(PythonScriptTask, self).save(*args, **kwargs)
            id = self.pk
            
            # 更新任务状态
            task_status = TaskStatus.objects.get(task_id=id, task_type='python')
            task_status.task_name = self.name
            task_status.last_status = '更新任务成功'
            task_status.last_run = datetime.now()
            task_status.task_status = 0 if self.is_enabled else 1
            task_status.save()
            
            # 更新调度器
            if self.is_enabled:
                add_job(id, self.frequency, 'python',self.is_run_now)
            else:
                remove_job(id, 'python')
            
            logger.info('python_script_task_{}更新'.format(id))

    def delete(self, *args, **kwargs):
        from task.utils.scheduler import remove_job
        
        id = self.pk
        remove_job(id, 'python')
        
        TaskStatus.objects.filter(task_id=id, task_type='python').delete()
        Content.objects.filter(task_id=id, task_type='python').delete()
        
        logger.info('python_script_task_{}删除'.format(id))
        super(PythonScriptTask, self).delete(*args, **kwargs)

   