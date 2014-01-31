from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from ftw.participation.interfaces import IParticipationRegistry
from plone.app.workflow.interfaces import ISharingPageRole
from plone.registry.interfaces import IRegistry
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class LocalRolesForDisplay(object):
    """Vocabulary of local roles"""

    implements(IVocabularyFactory)

    def __call__(self, context, role_filter=None, filter_reader_role=True):
        """Get a list of roles, similar like @@sharing"""

        if role_filter is None:
            role_filter = ['Reviewer', ]

        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)
        if filter_reader_role and config.allow_multiple_roles:
            role_filter = role_filter + ['Reader']

        roles = []
        for name, utility in self.get_role_utilities(context, role_filter):
            roles.append(SimpleTerm(name, name, utility.title))

        roles.sort(lambda x, y: cmp(x.title, y.title))
        return SimpleVocabulary(roles)

    def get_role_utilities(self, context, exclude):
        context = aq_inner(context)
        portal_membership = getToolByName(context, 'portal_membership')

        for name, utility in getUtilitiesFor(ISharingPageRole):
            if name in exclude:
                continue

            permission = getattr(utility, 'required_permission', None)
            if not permission:
                allowed = True
            else:
                allowed = portal_membership.checkPermission(
                    permission, context)

            if allowed:
                yield name, utility


LocalRolesForDisplayFactory = LocalRolesForDisplay()
