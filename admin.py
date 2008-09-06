from wwu_housing.jobs.models import Job, Applicant, Application, Date, File, Component, Requirement
from wwu_housing.western_auth import admin

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'open_datetime', 'close_datetime', 'description', 'post_datetime')
    list_filter = ('open_datetime', 'close_datetime')
admin.site.register(Job, JobAdmin)


class ApplicantAdmin(admin.ModelAdmin):
    pass
admin.site.register(Applicant, ApplicantAdmin)


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'start_datetime', 'end_datetime')
    list_filter = ('job', 'start_datetime', 'end_datetime')
admin.site.register(Application, ApplicationAdmin)


class DateAdmin(admin.ModelAdmin):
    list_display = ('job', 'name', 'date', 'description')
    list_display_links = ('name',)
    list_filter = ('job', 'date')
admin.site.register(Date, DateAdmin)


class FileAdmin(admin.ModelAdmin):
    pass
admin.site.register(File, FileAdmin)


class ComponentAdmin(admin.ModelAdmin):
    pass
admin.site.register(Component, ComponentAdmin)


class RequirementAdmin(admin.ModelAdmin):
    pass
admin.site.register(Requirement, RequirementAdmin)

