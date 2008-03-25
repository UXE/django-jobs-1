from django.db import models
from wwu_housing.jobs.models import Application
from wwu_housing.keymanager.models import Building, Community


class Availability(models.Model):
    """Questions related to applicant's availability."""
    on_campus = models.BooleanField(verbose_name="Will you be living on campus next year?")
    on_campus_where = models.ForeignKey(Building)
    work_study = models.NullBooleanField(verbose_name="Do you anticipate having federal work study next year?")
    hours_available = models.PositiveSmallIntegerField(verbose_name="How many hours will you be available per week?", help_text="Please use a whole number from one to nineteen.")


class Reference(models.Model):
    """This describes people who can vouch for an applicant."""
    name = models.CharField(max_length=255, verbose_name="Reference's Name")
    phone = models.CharField(max_length=20, verbose_name="Reference's Phone Number")


class PlacementPreference(models.Model):
    """This allows applicants to select which communities they would like to work in the most."""
    community = models.ForeignKey(Community)
    rank = models.PositiveSmallIntegerField()


class EssayQuestion(models.Model):
    """Essay questions."""
    question = models.CharField(max_length=255)
    class Admin:
        pass

    def __unicode__(self):
        return self.question


class EssayResponse(models.Model):
    """Applicant responses to the essay questions."""
    question = models.ForeignKey(EssayQuestion)
    answer = models.TextField()


class ApplicantStatus(models.Model):
    """This tracks the status of the application in each hall (e.g., "applied," "hired," etc.)."""
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
