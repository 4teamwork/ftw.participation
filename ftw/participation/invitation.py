from Products.CMFCore.utils import getToolByName
from ftw.participation.interfaces import IInvitation, IInvitationStorage
from persistent import Persistent
from plone.uuid.interfaces import IUUID
from zope.component.hooks import getSite
from zope.interface import implements


class Invitation(Persistent):
    """The `Invitation` object is used for storing who has invited who for
    which context.

    """

    implements(IInvitation)

    def __init__(self, target, email, inviter, roles):
        """Creates a new `Invitation` on the `target` for `email`. The
        invitation was created by `inviter` (userid). Roles are the given
        additional roles for the user (email)
        """
        # get the storage
        storage = IInvitationStorage(target)
        # set the attributes
        self.email = email
        self.inviter = inviter
        self.set_target(target)
        self.roles = roles
        # generate the id, which sets it to self.iid
        storage.generate_iid_for(self)
        # register the invitation
        storage.add_invitation(self)

    def set_target(self, obj):
        """Sets the target to the given `obj`. Internally we store UIDs.
        """
        self._target = IUUID(obj)

    def get_target(self):
        """Returns the currently stored target or `None`
        """
        if '_target' not in dir(self):
            return None
        site = getSite()
        catalog = getToolByName(site, 'portal_catalog')

        result = catalog.unrestrictedSearchResults(UID=self._target)
        if len(result) != 1:
            return None
        else:
            brain, = result
            return site.unrestrictedTraverse(brain.getPath())
