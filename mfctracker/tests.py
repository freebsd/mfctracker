from django.test import TestCase, Client

from .utils import get_mfc_requirements

class TestUtils(TestCase):
    def test_mfc_requirements(self):
        requirements = get_mfc_requirements('x-mfc-with: r1, r2,r3 , 4,5')
        self.assertEqual(requirements, set(xrange(1,6)))
