import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.template.defaultfilters import slugify

from wwu_housing.library.models import Address


class Job(models.Model):
    """
    A set of information used to describe an available job as specified by one
    of the job administrators.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    post_datetime = models.DateTimeField(help_text="The date and time this job is to be posted online.")
    open_datetime = models.DateTimeField(help_text="The date and time this job posting opens.")
    close_datetime = models.DateTimeField(help_text="The date and time this job posting closes.")
    deadline = models.DateTimeField(help_text="The date and time applications are due.")
    contact_email = models.EmailField()
    contact_address = models.ForeignKey(Address)
    administrators = models.ManyToManyField(User)

    def __unicode__(self):
        return self.title

    def is_active(self):
        """Returns whether the job posting is currently active."""
        return self.open_datetime <= datetime.datetime.now() < self.close_datetime

    def is_open(self):
        """Returns whether the application deadline has passed or not."""
        return self.open_datetime <= datetime.datetime.now() < self.deadline


class Component(models.Model):
    """
    Represents a component of a job that an applicant may need to complete as
    part of their job application.

    A component has an optional foreign key relationship to an object that
    represents the component.  For example, an "essay" component might reference
    an EssayQuestion model.
    """
    # TODO: add custom manager to pull all required components?
    job = models.ForeignKey(Job)
    name = models.CharField(max_length=255)
    sequence_number = models.IntegerField()
    is_required = models.BooleanField(default=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")

    class Meta:
        ordering = ("sequence_number",)

    def __unicode__(self):
        return self.name


class Applicant(models.Model):
    """A user with contact information and data specific to being an applicant to a job."""
    user = models.ForeignKey(User, unique=True)

    def __unicode__(self):
        return self.user.get_full_name()


class Application(models.Model):
    """
    A relationship between an applicant and a job that represents the
    applicant's interest in the job.
    """
    applicant = models.ForeignKey(Applicant)
    job = models.ForeignKey(Job)
    start_datetime = models.DateTimeField(blank=True, editable=False, 
                                          help_text="The time when the applicant started the application.")
    end_datetime = models.DateTimeField(blank=True, null=True, 
                                        help_text="The time when the applicant submitted the application.")
    components = models.ManyToManyField(Component, through="ApplicationComponent")

    def __unicode__(self):
        return u"%s for %s" % (self.applicant, self.job)

    def save(self, *args, **kwargs):
        if not self.id:
            self.start_datetime = datetime.datetime.now()
        super(Application, self).save(*args, **kwargs) 


class ApplicationComponent(models.Model):
    """
    Represents the relationship between a job component and an application.  The
    relationship includes meta data about when the component was complete for
    the application.

    An application component has an optional foreign key relationship to an
    object that represents the applicant's response to the component.  For
    example, an applicant might respond to an "essay" component with an instance
    of EssayResponse.
    """
    application = models.ForeignKey(Application)
    component = models.ForeignKey(Component)
    activity_date = models.DateTimeField(editable=False)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey("content_type", "object_id")

    def save(self, *args, **kwargs):
        self.activity_date = datetime.datetime.now()
        super(ApplicationComponent, self).save(*args, **kwargs)


class Date(models.Model):
    """Application-specific dates like deadlines and open and close dates."""
    job = models.ForeignKey(Job)
    name = models.CharField(max_length=255)
    slug = models.SlugField(editable=False)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u"%s: %s" % (self.job, self.name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Date, self).save(*args, **kwargs)


def file_upload_to(instance, filename):
    return "%s/%s" % (instance.applicant.id, filename)

class File(models.Model):
    """Files that can be used by an applicant for one or more applications."""
    applicant = models.ForeignKey(Applicant)
    name = models.CharField(max_length=255)
    path = models.FileField(upload_to=file_upload_to,
                            storage=FileSystemStorage(location="%s/jobs" % 
                                                      settings.FILE_UPLOAD_ROOT,
                                                      base_url="/django/jobs/files/"),
                            )
    last_modified = models.DateTimeField(editable=False)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.last_modified = datetime.datetime.now()
        super(File, self).save(*args, **kwargs)


class Qualification(models.Model):
    """
    A reference to a function which can be used to determine whether an
    applicant is qualified to apply for the job.
    """
    job = models.ForeignKey(Job)
    function_name = models.CharField(max_length=255,
                                     help_text="""The name of a function in the
                                     job's requirements.py which returns true or
                                     false when given an Applicant object.""")
