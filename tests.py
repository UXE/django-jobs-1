import datetime
from django import test
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
import httplib

from wwu_housing.tests import BaseTestCase
from wwu_housing.jobs import ComponentRegistry

from models import Applicant, Application, Job
from utils import assign_reviewers


class MockApplicant(object):
    def __init__(self, name):
        self.name = name


class MockReviewer(object):
    def __init__(self, name):
        self.name = name


class AssignReviewersTestCase(test.TestCase):
    """
    Test the function to assign an iterable of reviewer objects to an iterable
    of applicant objects.
    """
    def setUp(self):
        self.reviewers = [MockReviewer("Nick"), MockReviewer("Brian")]
        self.applicants = [MockApplicant("John"), MockApplicant("Firass")]
        self.get_reviewer_key = lambda r: r.name

    def tearDown(self):
        pass

    def test_no_rules(self):
        """
        Tests without any rules which behaves the same as if all rules returned
        True.
        """
        assignments = assign_reviewers(self.reviewers, self.applicants,
                                       get_reviewer_key=self.get_reviewer_key)
        unassigned_applicants = assignments.get("_UNASSIGNED", [])
        self.assertEqual(len(unassigned_applicants), 0)

    def test_false_rule(self):
        """
        Tests with a rule that always returns false such that no applicants are
        assigned.
        """
        assignments = assign_reviewers(self.reviewers, self.applicants,
                                       get_reviewer_key=self.get_reviewer_key,
                                       rules=[lambda r, a, c: False])
        unassigned_applicants = assignments.get("_UNASSIGNED", [])
        self.assertEqual(len(unassigned_applicants), len(self.applicants))

    def test_true_rule(self):
        """
        Tests with a rule always returns true, so all applicants get assigned.
        """
        assignments = assign_reviewers(self.reviewers, self.applicants,
                                       get_reviewer_key=self.get_reviewer_key,
                                       rules=[lambda r, a, c: True])
        unassigned_applicants = assignments.get("_UNASSIGNED", [])
        self.assertEqual(len(unassigned_applicants), 0)

    def test_two_reviewers_per_applicant(self):
        """
        Assigns two reviewers to each applicant.
        """
        applicants = self.applicants
        applicants_per_reviewer = len(self.applicants) / len(self.reviewers) * 2

        def two_reviewers_rule(reviewer, applicant, current_applicants):
            if (len(current_applicants) < applicants_per_reviewer and applicant not in current_applicants):
                return True
            return False

        assignments = assign_reviewers(self.reviewers, self.applicants,
                                       get_reviewer_key=self.get_reviewer_key,
                                       rules=[two_reviewers_rule])
        reviewers_by_applicant = {}
        for reviewer, apps in assignments.items():
            for app in apps:
                if not app in reviewers_by_applicant:
                    reviewers_by_applicant[app.name] = []
                reviewers_by_applicant[app.name].append(reviewer)

        self.assertTrue(all([len(reviewers) == 2
                             for reviewers in reviewers_by_applicant.values()]),
                        reviewers_by_applicant)


class FakeClass(object):
    pass


class ComponentRegistryTestCase(test.TestCase):
    """
    Tests for registry
    """
    def setUp(self):
        self.registry = ComponentRegistry()
        self.instance = FakeClass()

    def test_register(self):
        self.registry.register("component", "test", self.instance)
        self.assertTrue("component" in self.registry)

    def test_get(self):
        self.registry.register("component", "test", self.instance)
        self.assertEqual(1, len(self.registry.get("component")))
        self.assertTrue("test" in self.registry.get("component"))

    def test_register_multiple(self):
        self.registry.register("component", "test", self.instance)
        instance_two = FakeClass()
        self.registry.register("component", "test_two", instance_two)
        self.assertEqual(len(self.registry.get("component")), 2)

    def test_reregister(self):
        """
        Registry shouldn't allow a registered key's value to be overwritten.
        """
        self.registry.register("component", "test", self.instance)
        instance_two = FakeClass()
        self.assertRaises(
            ComponentRegistry.AlreadyRegistered,
            self.registry.register,
            "component",
            "test",
            instance_two
        )

    def test_get_not_registered(self):
        self.assertRaises(
            ComponentRegistry.NotRegistered,
            self.registry.get,
            "test"
        )


class JobTestCase(BaseTestCase):
    fixtures = ["jobs.json"]

    @classmethod
    def create_unpublished_job(cls, job):
        """
        Returns an unpublished job using the given job instance.
        """
        job.post_datetime = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        )
        job.save()
        return job

    @classmethod
    def create_published_job(cls, job):
        """
        Returns an published job using the given job instance.
        """
        job.close_datetime = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        )
        job.post_datetime = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        )
        job.save()
        return job

    @classmethod
    def create_unopened_job(cls, job):
        """
        Returns a published job that hasn't opened yet.
        """
        job = cls.create_published_job(job)
        job.open_datetime = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        )
        job.deadline = (
            datetime.datetime.now() + datetime.timedelta(days=2)
        )
        job.save()
        return job

    def setUp(self):
        super(JobTestCase, self).setUp()
        self.job = Job.objects.all()[0]

    def test_new_job(self):
        # Create a new job.
        self.job.id = None
        self.job.slug = None
        self.job.save()

        # Confirm new job has a slug based on the title.
        self.assertEqual(slugify(self.job.title), self.job.slug)

    def test_unpublished_job(self):
        # Create an unpublished job.
        self.job = JobTestCase.create_unpublished_job(self.job)

        # Confirm the job doesn't appear on the jobs page.
        response = self.get("jobs_index")
        self.assertEqual(httplib.OK, response.status_code)
        self.assertFalse(self.job.title in response.content)

        # Confirm the job website doesn't exist.
        response = self.get("jobs_job", self.job.slug)
        self.assertEqual(httplib.NOT_FOUND, response.status_code)

    def test_published_job(self):
        # Create a published job.
        self.job = JobTestCase.create_published_job(self.job)

        # Confirm the job appears on the jobs page.
        response = self.get("jobs_index")
        self.assertEqual(httplib.OK, response.status_code)
        self.assertTrue(self.job.title in response.content)

        # Confirm the job website exists.
        response = self.get("jobs_job", self.job.slug)
        self.assertEqual(httplib.OK, response.status_code)

        # Confirm the job title is in the job website's response.
        self.assertTrue(self.job.title in response.content)

    def test_get_absolute_url(self):
        self.assertTrue(self.job.slug in self.job.get_absolute_url())
        response = self.client.get(self.job.get_absolute_url())
        self.assertEqual(httplib.OK, response.status_code)

    def test_application_url(self):
        # Confirm the job application site exists.
        response = self.client.get(self.job.get_application_url())
        self.assertEqual(httplib.OK, response.status_code)

        # Confirm the job title appears on the application site.
        self.assertTrue(self.job.title in response.content)


class ApplicationTestCase(BaseTestCase):
    fixtures = ["jobs.json", "users.json"]

    def setUp(self):
        super(ApplicationTestCase, self).setUp()
        self.job = Job.objects.all()[0]
        self.user = User.objects.all()[0]
        self.applicant = Applicant.objects.create(user=self.user)

    def test_early_application(self):
        # Create an unopened job.
        self.job = JobTestCase.create_unopened_job(self.job)

        # Try to open an application before the application period has started.
        # Confirm application site isn't available (i.e., it redirects).
        self.assertRedirects(
            self.client.get(self.job.get_application_url()),
            self.job.get_absolute_url()
        )

        # # Confirm user gets an appropriate message about the application's
        # # status.
        # response = self.client.get(self.job.get_absolute_url())
        # self.assertContains(response, "open yet", msg_prefix=response.content)

        # Confirm an application wasn't created.
        self.assertRaises(
            Application.DoesNotExist,
            self.applicant.get_application_by_job,
            self.job
        )

    def test_new_application(self):
        # Open an application for the first time.

        # Confirm that an Applicant was created for the user.

        # Confirm that an Application was created for the applicant and the job.
        pass

    def test_existing_application(self):
        # Confirm application exists already.

        # Open application site.

        # Confirm that only one application exists for the current user.
        pass

    def test_new_application_after_deadline(self):
        # Set deadline on job.

        # Open application site.

        # Confirm application site redirects to job's site.

        # Confirm no application exists for user.
        pass

    def test_existing_application_after_deadline(self):
        # Set deadline on job.

        # Open application site.

        # Confirm application site loads.

        # Confirm there isn't a submit button in the application site response.
        pass

    def test_new_application_after_closed_job(self):
        # Set close date on job.

        # Open application site.

        # Confirm application site isn't available.
        pass

    def test_existing_application_after_closed_job(self):
        # Confirm application exists for current user.

        # Set close date on job.

        # Open application site.

        # Confirm application site isn't available.
        pass

    def test_component(self):
        # Create component for job.

        # Open component site.

        # Confirm component site is available.

        # Confirm component name is in the component site response.
        pass

    def test_submit_component(self):
        # Create a component for job.

        # POST data to the component site.

        # Confirm application component parts exist for the component and the
        # current user.
        pass

    def test_submit_incomplete_application(self):
        # Confirm an incomplete application exists for the current user.

        # POST data to the application site to submit application.

        # Confirm application has not been submitted.
        pass

    def test_submit_complete_application(self):
        # Confirm a complete application exists for the current user.

        # POST data to the application site to submit application.

        # Confirm application has been submitted.
        pass
