from __future__ import with_statement
import datetime
from django import test
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
import httplib

from wwu_housing.tests import BaseTestCase
from wwu_housing.jobs import ComponentRegistry

from models import Applicant, Application, Component, Job
from utils import assign_reviewers


# class MockApplicant(object):
#     def __init__(self, name):
#         self.name = name


# class MockReviewer(object):
#     def __init__(self, name):
#         self.name = name


# class AssignReviewersTestCase(test.TestCase):
#     """
#     Test the function to assign an iterable of reviewer objects to an iterable
#     of applicant objects.
#     """
#     def setUp(self):
#         self.reviewers = [MockReviewer("Nick"), MockReviewer("Brian")]
#         self.applicants = [MockApplicant("John"), MockApplicant("Firass")]
#         self.get_reviewer_key = lambda r: r.name

#     def tearDown(self):
#         pass

#     def test_no_rules(self):
#         """
#         Tests without any rules which behaves the same as if all rules returned
#         True.
#         """
#         assignments = assign_reviewers(self.reviewers, self.applicants,
#                                        get_reviewer_key=self.get_reviewer_key)
#         unassigned_applicants = assignments.get("_UNASSIGNED", [])
#         self.assertEqual(len(unassigned_applicants), 0)

#     def test_false_rule(self):
#         """
#         Tests with a rule that always returns false such that no applicants are
#         assigned.
#         """
#         assignments = assign_reviewers(self.reviewers, self.applicants,
#                                        get_reviewer_key=self.get_reviewer_key,
#                                        rules=[lambda r, a, c: False])
#         unassigned_applicants = assignments.get("_UNASSIGNED", [])
#         self.assertEqual(len(unassigned_applicants), len(self.applicants))

#     def test_true_rule(self):
#         """
#         Tests with a rule always returns true, so all applicants get assigned.
#         """
#         assignments = assign_reviewers(self.reviewers, self.applicants,
#                                        get_reviewer_key=self.get_reviewer_key,
#                                        rules=[lambda r, a, c: True])
#         unassigned_applicants = assignments.get("_UNASSIGNED", [])
#         self.assertEqual(len(unassigned_applicants), 0)

#     def test_two_reviewers_per_applicant(self):
#         """
#         Assigns two reviewers to each applicant.
#         """
#         applicants = self.applicants
#         applicants_per_reviewer = len(self.applicants) / len(self.reviewers) * 2

#         def two_reviewers_rule(reviewer, applicant, current_applicants):
#             if (len(current_applicants) < applicants_per_reviewer and applicant not in current_applicants):
#                 return True
#             return False

#         assignments = assign_reviewers(self.reviewers, self.applicants,
#                                        get_reviewer_key=self.get_reviewer_key,
#                                        rules=[two_reviewers_rule])
#         reviewers_by_applicant = {}
#         for reviewer, apps in assignments.items():
#             for app in apps:
#                 if not app in reviewers_by_applicant:
#                     reviewers_by_applicant[app.name] = []
#                 reviewers_by_applicant[app.name].append(reviewer)

#         self.assertTrue(all([len(reviewers) == 2
#                              for reviewers in reviewers_by_applicant.values()]),
#                         reviewers_by_applicant)


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
    def create_unpublished_job(cls, job, commit=True):
        """
        Returns an unpublished job.
        """
        job.post_datetime = (
            datetime.datetime.now() + datetime.timedelta(days=3)
        )

        if commit:
            job.save()

        return job

    @classmethod
    def create_published_job(cls, job, commit=True):
        """
        Returns an published job.
        """
        job.close_datetime = (
            datetime.datetime.now() + datetime.timedelta(days=3)
        )
        job.post_datetime = (
            datetime.datetime.now() - datetime.timedelta(days=3)
        )

        if commit:
            job.save()

        return job

    @classmethod
    def create_unopened_job(cls, job, commit=True):
        """
        Returns a published job that hasn't opened yet.
        """
        job = cls.create_published_job(job, commit=False)
        job.open_datetime = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        )
        job.deadline = (
            datetime.datetime.now() + datetime.timedelta(days=2)
        )

        if commit:
            job.save()

        return job

    @classmethod
    def create_opened_job(cls, job, commit=True):
        """
        Returns a published and opened job.
        """
        job = cls.create_unopened_job(job, commit=False)
        job.open_datetime = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        )
        job.deadline = (
            datetime.datetime.now() + datetime.timedelta(days=1)
        )

        if commit:
            job.save()

        return job

    @classmethod
    def create_deadlined_job(cls, job, commit=True):
        """
        Returns a job whose deadline has passed.
        """
        job = cls.create_unopened_job(job, commit=False)
        job.open_datetime = (
            datetime.datetime.now() - datetime.timedelta(days=2)
        )
        job.deadline = (
            datetime.datetime.now() - datetime.timedelta(days=1)
        )

        if commit:
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

    def test_is_open(self):
        # Test an unopened job.
        job = JobTestCase.create_unopened_job(self.job)
        self.assertFalse(job.is_open())

        # Test an opened job.
        job = JobTestCase.create_opened_job(self.job)
        self.assertTrue(job.is_open())

    def test_will_open(self):
        # Test an unopened job.
        job = JobTestCase.create_unopened_job(self.job)
        self.assertTrue(job.will_open())

        # Test an opened job.
        job = JobTestCase.create_opened_job(self.job)
        self.assertFalse(job.will_open())

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

    def test_opened_job(self):
        # Create a published job.
        self.job = JobTestCase.create_opened_job(self.job)

        # Confirm the job application link appears on the job page.
        response = self.client.get(self.job.get_absolute_url())
        self.assertTrue(self.job.get_application_url() in response.content)

    def test_get_absolute_url(self):
        self.assertTrue(self.job.slug in self.job.get_absolute_url())
        response = self.client.get(self.job.get_absolute_url())
        self.assertEqual(httplib.OK, response.status_code)


class ApplicationTestCase(BaseTestCase):
    fixtures = ["jobs.json", "users.json"]

    def setUp(self):
        super(ApplicationTestCase, self).setUp()
        self.job = Job.objects.all()[0]
        self.user = User.objects.all()[0]
        self.password = "test0r"
        self.user.set_password(self.password)
        self.user.save()
        self.applicant = Applicant.objects.create(user=self.user)

    def test_application_url(self):
        # Create an opened job.
        self.job = JobTestCase.create_opened_job(self.job)

        # Confirm the job application site exists.
        with self.login(self.user.username, self.password):
            response = self.client.get(self.job.get_application_url())
            self.assertEqual(httplib.OK, response.status_code)

            # Confirm the job title appears on the application site.
            self.assertTrue(self.job.title in response.content)

    def test_early_application(self):
        # Create an unopened job.
        self.job = JobTestCase.create_unopened_job(self.job)

        # Try to open an application before the application period has started.
        # Confirm application site isn't available (i.e., it redirects).
        with self.login(self.user.username, self.password):
            # Follow the redirect to get the content of the page we're
            # redirected to.
            response = self.client.get(self.job.get_application_url(), follow=True)
            self.assertRedirects(
                response,
                self.job.get_absolute_url()
            )

            # Confirm user gets an appropriate message about the application's
            # status.
            self.assertContains(response, "open yet")

        # Confirm an application wasn't created.
        self.assertRaises(
            Application.DoesNotExist,
            self.applicant.get_application_by_job,
            self.job
        )

    def test_new_applicant(self):
        # Create an opened job.
        self.job = JobTestCase.create_opened_job(self.job)

        # Confirm there is no applicant.
        self.applicant.delete()

        # Open an application for the first time.
        with self.login(self.user.username, self.password):
            response = self.client.get(self.job.get_application_url())
            self.assertEqual(httplib.OK, response.status_code)

        # Confirm that an Applicant was created for the user.
        self.assertEqual(1, self.user.applicant_set.count())

    def test_new_application(self):
        # Create an opened job.
        self.job = JobTestCase.create_opened_job(self.job)

        # Confirm there is no application for the applicant and the job.
        self.assertRaises(
            Application.DoesNotExist,
            self.applicant.get_application_by_job,
            self.job
        )

        # Open an application for the first time.
        with self.login(self.user.username, self.password):
            response = self.client.get(self.job.get_application_url())
            self.assertEqual(httplib.OK, response.status_code)

        # Confirm that an Application was created for the applicant and the job.
        applicant = self.user.applicant_set.all()[0]
        applications = Application.objects.filter(
            applicant=applicant,
            job=self.job
        )
        self.assertEqual(1, applications.count())

    def test_existing_application(self):
        # Create an opened job.
        self.job = JobTestCase.create_opened_job(self.job)

        # Confirm application exists already.
        application = Application.objects.create(
            applicant=self.applicant,
            job=self.job
        )

        # Open application site.
        with self.login(self.user.username, self.password):
            response = self.client.get(self.job.get_application_url())
            self.assertEqual(httplib.OK, response.status_code)

        # Confirm that only one application exists for the current user.
        applications = Application.objects.filter(
            applicant=self.applicant,
            job=self.job
        );
        self.assertEqual(1, applications.count())

    def test_new_application_after_deadline(self):
        # Create a job whose deadline has passed.
        self.job = JobTestCase.create_deadlined_job(self.job)

        # Confirm there is no application for this job and applicant.
        self.assertRaises(
            Application.DoesNotExist,
            self.applicant.get_application_by_job,
            self.job
        )

        # Confirm application site redirects to job's site.
        with self.login(self.user.username, self.password):
            response = self.client.get(self.job.get_application_url())
            self.assertRedirects(response, self.job.get_absolute_url())

        # Reconfirm no application exists for this job and applicant.
        self.assertRaises(
            Application.DoesNotExist,
            self.applicant.get_application_by_job,
            self.job
        )

    def test_existing_application_after_deadline(self):
        # Create a job whose deadline has passed.
        self.job = JobTestCase.create_deadlined_job(self.job)

        # Confirm an application exists.
        application = Application.objects.create(
            applicant=self.applicant,
            job=self.job
        )

        # Open application site.
        with self.login(self.user.username, self.password):
            # Confirm application site loads.
            response = self.client.get(self.job.get_application_url())
            self.assertEqual(httplib.OK, response.status_code)

            # Confirm there isn't a submit button in the application site
            # response.
            self.assertNotContains(response, "Submit application")

            # Confirm links don't exist for components to be edited.

    def test_new_application_after_closed_job(self):
        # Set close date on job.
        self.job = JobTestCase.create_opened_job(self.job)
        self.job.close_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        self.job.save()
        # Open application site.
        with self.login(self.user.username, self.password):
        # Confirm application site isn't available.
            response = self.client.get(self.job.get_application_url())
            self.assertRedirects(response, reverse("jobs_index"))

    def test_existing_application_after_closed_job(self):
        # Confirm application exists for current user.
        application = Application.objects.create(
            applicant=self.applicant,
            job=self.job
        )
        # Set close date on job.
        self.job.close_datetime = datetime.datetime.now() - datetime.timedelta(days=1)
        self.job.save()
        # Open application site.
        with self.login(self.user.username, self.password):
        # Confirm application site isn't available.
            response = self.client.get(self.job.get_application_url())
            self.assertRedirects(response, reverse("jobs_index"))

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


class ComponentTestCase(BaseTestCase):
    fixtures = ["jobs.json", "users.json"]

    def setUp(self):
        super(ComponentTestCase, self).setUp()
        self.job = Job.objects.all()[0]
        self.job = JobTestCase.create_opened_job(self.job)
        self.user = User.objects.all()[0]
        self.password = "test0r"
        self.user.set_password(self.password)
        self.user.save()
        self.applicant = Applicant.objects.create(user=self.user)
        self.application = Application.objects.create(
            job=self.job,
            applicant=self.applicant
        )
        self.component = Component.objects.create(
            job=self.job,
            name="Fake",
            sequence_number=1
        )

    def test_slug(self):
        # Confirm a slug was created.
        self.assertEqual(slugify(self.component.name), self.component.slug)

    def test_get_absolute_url(self):
        # Confirm the job and component slugs are in the component url.
        self.assertTrue(self.job.slug in self.component.get_absolute_url())
        self.assertTrue(self.component.slug in self.component.get_absolute_url())

    def test_nonexistent_component(self):
        # Delete existing component.
        self.component.delete()

        # Make an unsaved component (so we have to pass the slug).
        component = Component(
            job=self.job,
            name="Fake",
            slug="fake",
            sequence_number=1
        )

        # Try to load the nonexistent component.
        with self.login(self.user.username, self.password):
            response = self.client.get(component.get_absolute_url())
            self.assertEqual(httplib.NOT_FOUND, response.status_code)

    def test_component(self):
        # Open component site.
        with self.login(self.user.username, self.password):
            # Confirm component site is available.
            response = self.client.get(self.component.get_absolute_url())
            self.assertEqual(httplib.OK, response.status_code)

            # Confirm component name is in the component site response.
            self.assertContains(response, self.component.name)

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
