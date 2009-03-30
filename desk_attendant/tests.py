import datetime

from django import test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from wwu_housing.jobs.models import Job, Applicant, Application
from wwu_housing.desk_attendant.forms import *


class ApplicationAccessTestCase(test.TestCase):
    def setUp(self):
        # Setup the test client and log a user in.
        self.client = test.Client()
        self.client.login(student_id=u'W00588475', birth_date=datetime.date(1983, 2, 4))

        # Load a desk attendant job and the user associated with the Western id above.
        self.job = Job.objects.filter(title='Desk Attendant').latest('open_datetime')
        self.user = User.objects.get(username='huddlej')

    def test_closed_job(self):
        """Tests whether user is redirected to index."""
        # Close DA job.
        self.job.close_datetime = datetime.datetime.now()
        self.job.save()

        # Access the closed job application.
        response = self.client.get(reverse('wwu_housing.desk_attendant.views.apply'))
        
        # Verify the user is redirected to the index.
        self.assertEquals(302, response.status_code)
        self.assertTrue(response['location'].endswith('/django/jobs/desk-attendant/'))

    def test_no_previous_applicant_record(self):
        """Tests whether an applicant instance is created using request.user."""
        # Try to load an applicant record for the user.
        try:
            applicant = Applicant.objects.get(user=self.user)
            self.fail("Found an unexpected Applicant object for user %s." % self.user)
        except Applicant.DoesNotExist:
            pass

        # Access the DA application.
        response = self.client.get(reverse('wwu_housing.desk_attendant.views.apply'))
        self.failUnlessEqual(200, response.status_code)

        # Load the applicant record which should now exist for the user.
        applicant = Applicant.objects.get(user=self.user)

    def test_no_previous_application_record(self):
        """Tests whether an application instance is created using the proper Applicant and Job."""
        # Create an applicant record for the user.
        applicant = Applicant.objects.create(user=self.user)

        # Try to load an application record for the user.
        try:
            applicant = Application.objects.get(applicant=applicant, job=self.job)
            self.fail("Found an unexpected Application object for user %s." % self.user)
        except Application.DoesNotExist:
            pass

        # Access the DA application.
        response = self.client.get(reverse('wwu_housing.desk_attendant.views.apply'))
        self.failUnlessEqual(200, response.status_code)

        # Load the application record which should now exist for the user.
        applicant = Application.objects.get(applicant=applicant, job=self.job)


class FormTestCase(test.TestCase):
    def setUp(self):
        pass

    def test_availability_form(self):
        # Load an empty form.
        form = AvailabilityForm({})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors.has_key('hours_available'))

        # Load a form with the proper fields filled out, but with invalid data.
        form = AvailabilityForm({'hours_available': 20})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors.has_key('hours_available'))
        self.assertTrue('less than or equal to 19' in form.errors['hours_available'][0])

        form = AvailabilityForm({'hours_available': 0})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors.has_key('hours_available'))
        self.assertTrue('greater than or equal to 1' in form.errors['hours_available'][0])
        
        # Load a valid form.
        form = AvailabilityForm({'hours_available': 19})
        self.assertTrue(form.is_valid())

    def test_reference_form(self):
        # Load an empty form.  There should be no errors.
        form = ReferenceForm({})
        self.assertTrue(form.is_valid())
        
        # Test the form with both combinations of one empty field and one filled field.
        form = ReferenceForm({'name': 'Testor'})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.non_field_errors()) > 0)
        self.assertTrue('both fields' in form.non_field_errors()[0])

        form = ReferenceForm({'phone': '123-4567'})
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.non_field_errors()) > 0)
        self.assertTrue('both fields' in form.non_field_errors()[0])

        # Test the form with both fields filled.
        form = ReferenceForm({'name': 'Testor', 'phone': '123-4567'})
        self.assertTrue(form.is_valid())

    def test_placement_preference_form(self):
        pass

    def test_essay_response_form(self):
        pass

    def test_save_incomplete_application(self):
        """Verifies that no application elements are saved if not all validate."""
        # Post an empty form for the DA application which should generate errors.
        response = self.client.post(reverse('wwu_housing.desk_attendant.views.apply'), {})
        self.assertEquals(200, response.status_code)       

    def test_save_complete_application(self):
        """Verifies that all application elements are saved when all elements validate."""
        # All that is required for a complete application is hours of availability and
        # a mailing address and phone number.
        response = self.client.post(reverse('wwu_housing.desk_attendant.views.apply'), 
                                    {'hours_available': 19, 
                                     'current-address-street_line_1': '123 Fake St.',
                                     'current-address-city': 'Bellingham',
                                     'current-address-district': 'WA',
                                     'current-address-zip': '98225',
                                     'current-phone-phone': '123-4567'})
        self.assertEquals(302, response.status_code)
        self.assertTrue(response['location'].endswith('/django/jobs/desk-attendant/'))

