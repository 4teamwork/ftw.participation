from ftw.participation.activity.utils import translate_and_join_roles
from ftw.participation.tests import FunctionalTestCase


class TestInvitationRenderer(FunctionalTestCase):

    def test_translate_and_join_roles__1_role(self):
        self.assertEquals(
            'Can add',
            translate_and_join_roles(('Contributor',), None, None))

    def test_translate_and_join_roles__2_roles(self):
        self.assertEquals(
            'Can add and Can view',
            translate_and_join_roles(('Reader', 'Contributor'), None, None))

    def test_translate_and_join_roles__3_roles(self):
        self.assertEquals(
            'Can add, Can edit and Can view',
            translate_and_join_roles(('Reader', 'Editor', 'Contributor'), None, None))

    def test_translate_and_join_roles__4_roles(self):
        self.assertEquals(
            'Can add, Can edit and Can view',
            translate_and_join_roles(
                ('Reader', 'Editor', 'Contributor', 'Manager'), None, None))
