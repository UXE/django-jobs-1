from django import test

from wwu_housing.jobs import ComponentRegistry

from utils import assign_reviewers


class Applicant(object):
    def __init__(self, name):
        self.name = name


class Reviewer(object):
    def __init__(self, name):
        self.name = name


class AssignReviewersTestCase(test.TestCase):
    """
    Test the function to assign an iterable of reviewer objects to an iterable
    of applicant objects.
    """
    def setUp(self):
        self.reviewers = [Reviewer("Nick"), Reviewer("Brian")]
        self.applicants = [Applicant("John"), Applicant("Firass")]
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


class JobTestCase(test.TestCase):
    def test_unpublished_job(self):
        # Create an unpublished job.

        # Confirm the job doesn't appear on the jobs page.

        # Confirm the job website doesn't exist.
        pass

    def test_published_job(self):
        # Create a published job.

        # Confirm the job appears on the jobs page.

        # Confirm the job website exists.

        # Confirm the job title is in the job website's response.
        pass

    def test_early_application(self):
        # Try to open an application before the application period has started.

        # Confirm application site isn't available.

        # Confirm an application wasn't created.
        pass

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

    def test_closed_application(self):

        pass
