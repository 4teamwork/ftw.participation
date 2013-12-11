from ftw.participation.interfaces import IParticipationRegistry
from ftw.participation.tests.layer import FTW_PARTICIPATION_INTEGRATION_TESTING
from plone.app.workflow.interfaces import ISharingPageRole
from plone.app.workflow.permissions import DelegateContributorRole
from plone.registry.interfaces import IRegistry
from unittest2 import TestCase
from zope.component import getSiteManager
from zope.component import getUtility
from zope.i18nmessageid import Message
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory


def as_dict(vocabulary):
    """Converts a simple vocabulary to a dict, using the tokens as key.
    """
    return dict([(term.token, term.title) for term in vocabulary])


class Tester(object):
    implements(ISharingPageRole)

    title = 'Can test'


class TestLocalRolesForDisplay(TestCase):

    layer = FTW_PARTICIPATION_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_Reviewer_role_is_excluded_by_default(self):
        self.assertNotIn('Reviewer',
                         as_dict(self.factory(self.portal)))

    def test_Reviewer_role_can_be_included_by_resetting_filters(self):
        self.assertIn('Reviewer',
                      as_dict(self.factory(self.portal, role_filter=[])))

    def test_Reader_role_is_excluded_by_default(self):
        self.assertNotIn('Reader',
                         as_dict(self.factory(self.portal)))

    def test_filter_reader_role_excludes_Reader_role(self):
        self.assertIn('Reader',
                      as_dict(self.factory(self.portal, filter_reader_role=False)))

    def test_allow_multiple_roles_option_required_for_filter_reader_role(self):
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        config.allow_multiple_roles = False

        self.assertIn('Reader',
                      as_dict(self.factory(self.portal, filter_reader_role=True)))

    def test_role_permissions_are_checked(self):
        self.assertIn('Contributor',
                      as_dict(self.factory(self.portal)))

        self.portal.manage_permission(DelegateContributorRole, roles=[], acquire=False)
        self.assertNotIn('Contributor',
                         as_dict(self.factory(self.portal)))

    def test_titles_are_translation_messages(self):
        contributor = as_dict(self.factory(self.portal))['Contributor']
        self.assertEquals(Message, type(contributor))
        self.assertEquals('Can add', contributor.default)

    def test_roles_without_permission_are_listed(self):
        getSiteManager().registerUtility(provided=ISharingPageRole,
                                         factory=Tester,
                                         name='Tester')
        self.assertIn('Tester',
                      as_dict(self.factory(self.portal)))

    @property
    def factory(self):
        return getUtility(IVocabularyFactory, name='ftw.participation.roles')
