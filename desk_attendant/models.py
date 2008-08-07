import os

from django.conf import settings
from django.db import models
from django.db.models import ImageField

from wwu_housing import models as custom_models
from wwu_housing.jobs.models import Application
from wwu_housing.keymanager.models import Building, Community


class Availability(models.Model):
    """Questions related to applicant's availability."""
    application = models.ForeignKey(Application, unique=True)
    on_campus = models.BooleanField(verbose_name="Will you be living on campus next year?")
    on_campus_where = models.ForeignKey(Building, verbose_name="If yes, where?", blank=True, null=True)
    work_study = models.NullBooleanField(verbose_name="Do you anticipate having federal work study next year?")
    hours_available = models.PositiveSmallIntegerField(verbose_name="How many hours will you be available per week?", help_text="Please use a whole number from one to nineteen.")
    prior_desk_attendant = models.BooleanField(verbose_name="Are you a returning Desk Attendant?")

    class Meta:
        verbose_name_plural = 'availability'

    def __unicode__(self):
        return u"%s" % self.application

    def get_community_rank(self, community):
        community_preferences = PlacementPreference.objects.filter(application=self.application).filter(community=community)
        try:
            rank = community_preferences[0].rank
        except:
            return None
        return rank


class Reference(models.Model):
    """This describes people who can vouch for an applicant."""
    application = models.ForeignKey(Application)
    name = models.CharField(max_length=255, verbose_name="Reference Name", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Reference Phone Number", blank=True)

    def __unicode__(self):
        return u"Name: %s\nPhone: %s" % (self.name, self.phone)


class PlacementPreference(models.Model):
    """This allows applicants to select which communities they would like to work in the most."""
    application = models.ForeignKey(Application)
    community = models.ForeignKey(Community, blank=True)
    rank = models.PositiveSmallIntegerField(blank=True)

    class Meta:
        ordering = ('rank',)

    def __unicode__(self):
        return u"%i. %s" % (self.rank, self.community)


class EssayQuestion(models.Model):
    """Essay questions."""
    question = models.CharField(max_length=255)

    def __unicode__(self):
        return self.question


class EssayResponse(models.Model):
    """Applicant responses to the essay questions."""
    application = models.ForeignKey(Application)
    question = models.ForeignKey(EssayQuestion)
    answer = models.TextField()

    def __unicode__(self):
        return self.answer


# Shouldn't this be applicaTIONstatus?
class ApplicantStatus(models.Model):
    """This tracks the status of the application in each hall (e.g., "applied," "hired," etc.)."""
    application = models.ForeignKey(Application)
    community = models.ForeignKey(Community)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = (("application", "community", "name"),)
        verbose_name_plural = 'applicant statuses'

    def __unicode__(self):
        return "%s: %s %s" % (self.community, self.name, self.value)


class Resume(models.Model):
    application = models.ForeignKey(Application)
    resume = custom_models.SecureFileField(upload_to='deskattendant/resumes')

    # Override Django's curried get_FIELD methods so they return secure paths.

    def get_resume_filename(self):
        if self.resume: # value is not blank
            return os.path.join(settings.SECURE_MEDIA_ROOT, self.resume)
        return ''

    def get_resume_url(self):
        if self.resume: # value is not blank
            import urlparse
            return urlparse.urljoin(settings.SECURE_MEDIA_URL, self.resume).replace('\\', '/')
        return ''

    def get_resume_size(self):
        return os.path.getsize(self.get_resume_filename())

    def _save_FIELD_file(self, field, filename, raw_contents, save=True):
        directory = field.get_directory_name()
        try: # Create the date-based directory if it doesn't exist.
            os.makedirs(os.path.join(settings.SECURE_MEDIA_ROOT, directory))
        except OSError: # Directory probably already exists.
            pass
        filename = field.get_filename(filename)

        # If the filename already exists, keep adding an underscore to the name of
        # the file until the filename doesn't exist.
        while os.path.exists(os.path.join(settings.SECURE_MEDIA_ROOT, filename)):
            try:
                dot_index = filename.rindex('.')
            except ValueError: # filename has no dot
                filename += '_'
            else:
                filename = filename[:dot_index] + '_' + filename[dot_index:]

        # Write the file to disk.
        setattr(self, field.attname, filename)

        full_filename = self.get_resume_filename()
        fp = open(full_filename, 'wb')
        fp.write(raw_contents)
        fp.close()

        # Save the width and/or height, if applicable.
        if isinstance(field, ImageField) and (field.width_field or field.height_field):
            from django.utils.images import get_image_dimensions
            width, height = get_image_dimensions(full_filename)
            if field.width_field:
                setattr(self, field.width_field, width)
            if field.height_field:
                setattr(self, field.height_field, height)

        # Save the object because it has changed unless save is False
        if save:
            self.save()

    _save_FIELD_file.alters_data = True

    def __unicode__(self):
        return u'Resume for %s' % self.application.applicant 
