import logging

from django.contrib import admin, messages
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from task.models import Content, RSSTask, PageMonitorTask, TaskStatus, PythonScriptTask
from task.utils.scheduler import remove_job

logger = logging.getLogger('admin')


@admin.register(TaskStatus)
class TaskStatusAdmin(admin.ModelAdmin):
    list_display = [
        'task_name', 'last_run', 'short_last_status', 'task_status',
        'task_type'
    ]
    list_editable = ['task_status']
    list_per_page = 10
    list_display_links = None

    actions_on_top = True

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PageMonitorTaskResource(resources.ModelResource):
    class Meta:
        model = PageMonitorTask
        import_id_fields = ('name', )
        exclude = ('id', )
        skip_unchanged = True
        report_skipped = True


@admin.register(PageMonitorTask)
class PageMonitorTaskAdmin(ImportExportModelAdmin):
    resource_class = PageMonitorTaskResource

    list_display = [
        'id', 'name', 'url', 'frequency', 'selector', 'create_time',
        'is_chrome', 'regular_expression', 'rule', 'headers'
    ]
    list_editable = ('name', 'url', 'frequency', 'is_chrome',
                     'regular_expression', 'rule', 'headers', 'selector')
    filter_horizontal = ('notification', )

    list_per_page = 10

    def has_delete_permission(self, request, obj=None):
        return False

    def redefine_delete_selected(self, request, obj):
        for o in obj.all():
            id = o.id
            remove_job(id)

            TaskStatus.objects.filter(task_id=id, task_type='html').delete()
            Content.objects.filter(task_id=id, task_type='html').delete()

            o.delete()
            logger.info('task_{}删除(page_monitor)'.format(id))

        messages.add_message(request, messages.SUCCESS, '删除成功')

    redefine_delete_selected.short_description = '删除'
    redefine_delete_selected.icon = 'el-icon-delete'
    redefine_delete_selected.style = 'color:white;background:red'

    actions = ['redefine_delete_selected']


class RSSTaskResource(resources.ModelResource):
    class Meta:
        model = RSSTask
        import_id_fields = ('name', )
        exclude = ('id', )
        skip_unchanged = True
        report_skipped = True


@admin.register(RSSTask)
class RSSTaskAdmin(ImportExportModelAdmin):
    resource_class = RSSTaskResource

    list_display = ['id', 'name', 'url', 'frequency', 'create_time']
    list_editable = ('name', 'url', 'frequency')
    filter_horizontal = ('notification', )

    list_per_page = 10

    def has_delete_permission(self, request, obj=None):
        return False

    def redefine_delete_selected(self, request, obj):
        for o in obj.all():
            id = o.id
            remove_job(id, 'rss')

            TaskStatus.objects.filter(task_id=id, task_type='rss').delete()
            Content.objects.filter(task_id=id, task_type='rss').delete()

            o.delete()
            logger.info('task_rss{}删除'.format(id))

        messages.add_message(request, messages.SUCCESS, '删除成功')

    redefine_delete_selected.short_description = '删除'
    redefine_delete_selected.icon = 'el-icon-delete'
    redefine_delete_selected.style = 'color:white;background:red'

    actions = ['redefine_delete_selected']


class PythonScriptTaskResource(resources.ModelResource):
    class Meta:
        model = PythonScriptTask
        import_id_fields = ('name', )
        exclude = ('id', )
        skip_unchanged = True
        report_skipped = True


@admin.register(PythonScriptTask)
class PythonScriptTaskAdmin(ImportExportModelAdmin):
    resource_class = PythonScriptTaskResource

    list_display = [
        'id', 'name', 'script', 'description', 'frequency', 'timeout',  'create_time',
        'is_enabled','no_repeat'
    ]
    list_editable = ('name', 'script', 'description', 'frequency', 'timeout',
                     'is_enabled','no_repeat')
    filter_horizontal = ('notification', )


    list_per_page = 10

    def has_delete_permission(self, request, obj=None):
        return False

    def redefine_delete_selected(self, request, obj):
        for o in obj.all():
            id = o.id
            remove_job(id,'python')

            TaskStatus.objects.filter(task_id=id, task_type='python').delete()
            Content.objects.filter(task_id=id, task_type='python').delete()

            o.delete()
            logger.info('task_python{}删除'.format(id))

        messages.add_message(request, messages.SUCCESS, '删除成功')

    redefine_delete_selected.short_description = '删除'
    redefine_delete_selected.icon = 'el-icon-delete'
    redefine_delete_selected.style = 'color:white;background:red'

    actions = ['redefine_delete_selected']