from django.db import models
from wwu_housing.jobs.models import Application
from wwu_housing.keymanager.models import Building, Community


class Availability(models.Model):
    """Questions related to applicant's availability."""
    #application = models.ForeignKey(Application, unique=True)
    on_campus = models.BooleanField(verbose_name="Will you be living on campus next year?")
    on_campus_where = models.ForeignKey(Building, blank=True)
    work_study = models.NullBooleanField(verbose_name="Do you anticipate having federal work study next year?")
    hours_available = models.PositiveSmallIntegerField(verbose_name="How many hours will you be available per week?", help_text="Please use a whole number from one to nineteen.")
    class Admin:
        pass


class Reference(models.Model):
    """This describes people who can vouch for an applicant."""
    #application = models.ForeignKey(Application)
    name = models.CharField(max_length=255, verbose_name="Reference's Name")
    phone = models.CharField(max_length=20, verbose_name="Reference's Phone Number")
    class Admin:
        pass


class PlacementPreference(models.Model):
    """This allows applicants to select which communities they would like to work in the most."""
    #application = models.ForeignKey(Application)
    community = models.ForeignKey(Community)
    rank = models.PositiveSmallIntegerField()
    class Admin:
        pass


class EssayQuestion(models.Model):
    """Essay questions."""
    question = models.CharField(max_length=255)
    class Admin:
        pass

    def __unicode__(self):
        return self.question


class EssayResponse(models.Model):
    """Applicant responses to the essay questions."""
    #application = models.ForeignKey(Application)
    question = models.ForeignKey(EssayQuestion)
    answer = models.TextField()
    class Admin:
        pass


class ApplicantStatus(models.Model):
    """This tracks the status of the application in each hall (e.g., "applied," "hired," etc.)."""
    #application = models.ForeignKey(Application)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
    class Admin:
        pass
