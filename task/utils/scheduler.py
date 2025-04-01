import logging
import traceback
import multiprocessing
from datetime import datetime

import markdown
from apscheduler.jobstores.base import JobLookupError
from func_timeout.exceptions import FunctionTimedOut

from task.models import Content, RSSTask, PageMonitorTask, TaskStatus, PythonScriptTask
from task.utils.extract_info import get_content, get_rss_content
from task.utils.notification.notification_handler import new_handler
from task.utils.rule import is_changed
from task.views import scheduler

logger = logging.getLogger('main')


# 部分通知方式出错异常
class PartNotificationError(Exception):
    pass


def wraper_rss_msg(item):
    title = item['title']
    link = item['link']

    res = '''[{}]({})'''.format(title, link)
    return res


def send_message(content, header, notifications):
    if len(notifications) == 0:
        raise Exception('通知方式为空')

    total = 0
    fail = 0

    exception_content = ''
    for notification in notifications:
        total += 1

        type = notification.type
        notification_detail = notification.content

        try:
            if type == 0:
                handler = new_handler('mail')
                content = markdown.markdown(content,
                                            output_format='html5',
                                            extensions=['extra'])
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Mail Exception: {};'.format(repr(e))

        try:
            if type == 1:
                handler = new_handler('wechat')
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Wechat Exception: {};'.format(repr(e))

        try:
            if type == 2:
                handler = new_handler('pushover')
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Pushover Exception: {};'.format(repr(e))

        try:
            if type == 3:
                handler = new_handler('bark')
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Bark Exception: {};'.format(repr(e))

        try:
            if type == 4:
                handler = new_handler('custom')
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Custom Exception: {};'.format(repr(e))

        try:
            if type == 5:
                handler = new_handler('slack')
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Slack Exception: {};'.format(repr(e))

        try:
            if type == 6:
                handler = new_handler('telegram')
                handler.send(notification_detail, header, content)
        except Exception as e:
            fail += 1
            exception_content += 'Telegram Exception: {};'.format(repr(e))

    if fail > 0:
        if fail < total:
            raise PartNotificationError('监测到变化，部分通知方式发送错误：' +
                                        exception_content)
        else:
            raise Exception('监测到变化，但发送通知错误：' + exception_content)


def monitor(id, type):
    status = ''
    global_content = None
    last = None
    try:
        if type == 'html':
            task = PageMonitorTask.objects.get(pk=id)
            name = task.name
            url = task.url
            selector_type = task.selector_type
            selector = task.selector
            is_chrome = task.is_chrome
            content_template = task.template

            notifications = [i for i in task.notification.iterator()]

            regular_expression = task.regular_expression
            rule = task.rule
            headers = task.headers

            try:
                last = Content.objects.get(task_id=id, task_type=type)
            except Exception:
                last = Content(task_id=id)

            last_content = last.content
            content = get_content(url, is_chrome, selector_type, selector,
                                  content_template, regular_expression,
                                  headers)
            global_content = content
            status_code = is_changed(rule, content, last_content)
            logger.info(
                'rule: {}, content: {}, last_content: {}, status_code: {}'.
                format(rule, content, last_content, status_code))
            if status_code == 1:
                status = '监测到变化，但未命中规则，最新值为{}'.format(content)
                last.content = content
                last.save()
            elif status_code == 2:
                status = '监测到变化，且命中规则，最新值为{}'.format(content)
                send_message(content, name, notifications)
                last.content = content
                last.save()
            elif status_code == 3:
                status = '监测到变化，最新值为{}'.format(content)
                send_message(content, name, notifications)
                last.content = content
                last.save()
            elif status_code == 0:
                status = '成功执行但未监测到变化，当前值为{}'.format(content)
        elif type == 'rss':
            rss_task = RSSTask.objects.get(id=id)
            url = rss_task.url
            name = rss_task.name

            notifications = [i for i in rss_task.notification.iterator()]

            try:
                last = Content.objects.get(task_id=id, task_type=type)
            except Exception:
                last = Content(task_id=id, task_type='rss')

            last_guid = last.content
            item = get_rss_content(url)
            global_content = item['guid']
            if item['guid'] != last_guid:
                content = wraper_rss_msg(item)
                send_message(content, name, notifications)
                last.content = item['guid']
                last.save()
                status = '监测到变化，最新值：' + item['guid']
            else:
                status = '成功执行但未监测到变化，当前值为{}'.format(last_guid)

    except FunctionTimedOut:
        logger.error(traceback.format_exc())
        status = '解析RSS超时'
    except PartNotificationError as e:
        logger.error(traceback.format_exc())
        status = repr(e)
        last.content = global_content
        last.save()
    except Exception as e:
        logger.error(traceback.format_exc())
        status = repr(e)

    task_status = TaskStatus.objects.get(task_id=id, task_type=type)
    task_status.last_run = datetime.now()
    task_status.last_status = status
    task_status.save()


def add_job(id, interval, type='html'):
    task_id = ''
    if type == 'html':
        task_id = id
    elif type == 'rss':
        task_id = 'rss{}'.format(id)
    elif type == 'python':
        task_id = 'python{}'.format(id)
    try:
        scheduler.remove_job(job_id='task_{}'.format(task_id))
    except Exception:
        pass
    if type == 'python':
        scheduler.add_job(func=execute_python_script,
                        args=(
                            id,
                        ),
                        trigger='interval',
                        minutes=interval,
                        id='task_{}'.format(task_id),
                        replace_existing=True)
    else:
        scheduler.add_job(func=monitor,
                        args=(
                            id,
                            type,
                        ),
                        trigger='interval',
                        minutes=interval,
                        id='task_{}'.format(task_id),
                        replace_existing=True)
    logger.info('添加定时任务task_{}'.format(task_id))


def remove_job(id, type='html'):
    task_id = ''

    if type == 'html':
        task_id = id
    elif type == 'rss':
        task_id = 'rss{}'.format(id)
    elif type == 'python':
        task_id = 'python{}'.format(id)

    try:
        scheduler.remove_job('task_{}'.format(task_id))
        logger.info('删除定时任务task_{}'.format(task_id))
    except JobLookupError as e:
        logger.info(e)
        logger.info('task_{}不存在'.format(task_id))


def run_script(script):
        """在子进程中执行的函数"""
        try:
            # 初始化结果变量
            namespace = globals()
            
            # 执行用户脚本
            # 使用namespace作为全局命名空间
            # 第二个参数用户限制查询可以访问的模块或变量，这里不做限制
            exec(script, namespace)
            
            # 检查是否定义了result变量
            if 'result' not in namespace:
                return {
                    "status": "error",
                    "message": "脚本中没有定义result变量"
                }
            
            code_result = namespace['result']
            # 确保result是字典类型
            if not isinstance(code_result, str):
                return {
                    "status": "error",
                    "message": "代码里面的result变量必须是字符串类型"
                }
         
            return {
                    "status": "success",
                    "message": code_result
                }
         
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"脚本执行出错: {str(e)}"
            }
            
def execute_python_script(id):
    """执行Python脚本任"""
    status = ''
    global_content = None
    last = None
    try:
        # 获取任务信息
        task = PythonScriptTask.objects.get(id=id)
        # 获取任务所有配置参数
        name =task.name
        script = task.script
        notifications = [i for i in task.notification.iterator()]
        no_repeat = task.no_repeat
        timeout = task.timeout
        is_enabled = task.is_enabled

        # 如果任务未启用，则不执行 
        if not is_enabled:
            status = '任务未启用'
        else:
            try:
                last = Content.objects.get(task_id=id, task_type=type)
            except Exception:
                last = Content(task_id=id)
            last_content = last.content

            # 创建进程池
            pool = multiprocessing.Pool(processes=1)
        
            # 异步执行脚本
            async_result = pool.apply_async(run_script,args=(script,))
            
            # 等待执行结果，设置超时
            try:
                result = async_result.get(timeout=task.timeout)
            except multiprocessing.TimeoutError:
                result = {
                    "status": "error",
                    "message": f"脚本执行超时（{task.timeout}秒）"
                }
            finally:
                pool.close()
                pool.join()

            global_content = result.get('message', '')
            if no_repeat and global_content == last_content:
                status = '任务获取的结果和上一次相同，因为你启用了不重复，所以不发送消息'
            else:
                status = '任务执行成功，已发送通知'

            # 发送通知并记录执行结果
            logger.info(
                'content: {}, last_content: {}, status: {}'.
                format(global_content, last_content, status))
            send_message(global_content, name, notifications)
            last.content = global_content
            last.save()

    except Exception as e:
        logger.error(traceback.format_exc())
        status = repr(e)

    
    task_status = TaskStatus.objects.get(task_id=id, task_type='python')
    task_status.last_run = datetime.now()
    task_status.last_status = status
    task_status.save()