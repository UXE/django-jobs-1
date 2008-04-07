from django import test


class ApplicationAccessTestCase(test.TestCase):
    def setUp(self):
        pass

    def test_closed_job(self):
        """Tests whether user is redirected to index."""
        pass

    def test_no_previous_applicant_record(self):
        """Tests whether an applicant instance is created using request.user."""
        pass

    def test_no_previous_application_record(self):
        """Tests whether an application instance is created using the proper Applicant and Job."""
        pass


class FormTestCase(test.TestCase):
    def setUp(self):
        pass

    def test_availability_form(self):
        pass

    def test_reference_form(self):
        pass

    def test_placement_preference_form(self):
        pass

    def test_essay_response_form(self):
        pass

    def test_save_incomplete_application(self):
        """Verifies that no application elements are saved if not all validate."""
        pass

    def test_save_complete_application(self):
        """Verifies that all application elements are saved when all elements validate."""
        pass
