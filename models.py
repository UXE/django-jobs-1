import datetime
from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from wwu_housing.library.models import Address


class Job(models.Model):
    """A set of information used to describe an available job as specified by one of the job
    administrators.
    
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


class Applicant(models.Model):
    """A user with contact information and data specific to being an applicant to a job."""
    user = models.ForeignKey(User, unique=True)

    def __unicode__(self):
        try:
            if self.user.first_name and self.user.last_name:
                return u"%s, %s" % (self.user.last_name, self.user.first_name)
        except:
            pass
        return unicode(self.user)


class Application(models.Model):
    """A relationship between an applicant and a job that represents the applicant's interest in the job.

    # Create an application.
    >>> from wwu_housing.jobs.models import *
    >>> import datetime
    >>> applicant = Applicant.objects.all()[0]
    >>> job = Job.objects.all()[0]
    >>> application = Application.objects.create(job=job, applicant=applicant, start_datetime=datetime.datetime.now())
    >>> application.save()
    >>>
    # Make sure start timestamp was created.
    >>> assert application.start_timestamp is not None
    >>> 

    """
    applicant = models.ForeignKey(Applicant)
    job = models.ForeignKey(Job)
    start_datetime = models.DateTimeField(blank=True, editable=False, help_text="The time when the applicant started the application.")
    end_datetime = models.DateTimeField(blank=True, null=True, 
                                         help_text="The time when the applicant submitted the application.")

    def __unicode__(self):
        return u"%s for %s" % (self.applicant, self.job)

    def save(self, *args, **kwargs):
        if not self.id:
            self.start_datetime = datetime.datetime.now()
        super(Application, self).save(*args, **kwargs) 

#     def load_existing_application(self):
#         # Find components for the job.
#         components = self.job.component_set.all()
        
#         # Build a dictionary of lists of components.
#         application = {}
#         for component in components:
#             try:
#                 component_attribute = "%_set" % component.name.lower()
#                 if hasattr(self, component_attribute):
#                     application[component.name] = eval(self.component_attribute.all())
#             except:
#                 pass


class Date(models.Model):
    """Application-specific dates like deadlines and open and close dates."""
    job = models.ForeignKey(Job)
    name = models.CharField(max_length=255)
    date = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u"%s: %s" % (self.job, self.name)

    def save(self, *args, **kwargs):
        # Don't allow names to include spaces.
        self.name = self.name.replace(' ', '_')
        super(Date, self).save(*args, **kwargs)


class File(models.Model):
    """Files that can be used by an applicant for one or more applications."""
    applicant = models.ForeignKey(Applicant)
    name = models.CharField(max_length=255)
    path = models.FileField(upload_to='/jobs/') # TODO: This needs to upload to a non-MEDIA_ROOT directory.
    last_modified = models.DateTimeField(editable=False)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.last_modified = datetime.datetime.now()
        super(File, self).save(*args, **kwargs)


class Component(models.Model):
    """A reference to a Django model used by the job application and information about how
    the model's data should be displayed in the application as specified by the job's
    administrators.

    """
    job = models.ForeignKey(Job)
    name = models.CharField(max_length=255,
                            help_text="The name of any Django model available in the job's model namespace.")
    sequence_number = models.IntegerField()
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence_number']


class Requirement(models.Model):
    """A reference to a function which can be used to determine whether an applicant is qualified
    to apply for the job.

    """
    job = models.ForeignKey(Job)
    function_name = models.CharField(max_length=255, 
                                     help_text="The name of a function in the job's requirements.py which returns true or false when given an Applicant object.")
