from django.contrib import admin

from wwu_housing.desk_attendant.models import Availability, Reference, PlacementPreference
from wwu_housing.desk_attendant.models import EssayQuestion, EssayResponse, ApplicantStatus, Resume


class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('application', 'on_campus', 'on_campus_where', 'hours_available', 'prior_desk_attendant')
    list_filter = ('on_campus', 'on_campus_where', 'work_study', 'hours_available', 'prior_desk_attendant')
admin.site.register(Availability, AvailabilityAdmin)


class ReferenceAdmin(admin.ModelAdmin):
    list_display = ('application', 'name', 'phone')
admin.site.register(Reference, ReferenceAdmin)


class PlacementPreferenceAdmin(admin.ModelAdmin):
    list_display = ('application', 'community', 'rank')
admin.site.register(PlacementPreference, PlacementPreferenceAdmin)


class EssayQuestionAdmin(admin.ModelAdmin):
    pass
admin.site.register(EssayQuestion, EssayQuestionAdmin)


class EssayResponseAdmin(admin.ModelAdmin):
    list_display = ('application', 'question', 'answer')
admin.site.register(EssayResponse, EssayResponseAdmin)


class ApplicantStatusAdmin(admin.ModelAdmin):
    pass
admin.site.register(ApplicantStatus, ApplicantStatusAdmin)


class ResumeAdmin(admin.ModelAdmin):
    pass
admin.site.register(Resume, ResumeAdmin)

