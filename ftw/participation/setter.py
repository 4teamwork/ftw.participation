from ftw.participation import interfaces
from ftw.participation.interfaces import IParticipationRegistry
from plone.registry.interfaces import IRegistry
from zope.component import adapts
from zope.component import getUtility
from zope.interface import Interface
from zope.interface import implements
import AccessControl


class DefaultParticipationSetter(object):
    """Sets up a participation on a object for a user.
    Discriminators:
    - context
    - request
    - invitation
    - member

    """

    adapts(interfaces.IParticipationSupport,
           Interface,
           interfaces.IInvitation,
           Interface)

    implements(interfaces.IParticipationSetter)

    def __init__(self, context, request, invitation, member):
        self.context = context
        self.request = request
        self.invitation = invitation
        self.member = member

    def __call__(self):
        """Participates the user
        """
        return self.participate_user()

    def participate_user(self):
        """Participates `self.user` on `self.context`.
        """
        local_roles = dict(self.context.get_local_roles())
        # get all current local roles of the user on this context
        user_roles = list(local_roles.get(self.member.getId(), []))
        user_roles.extend(self.roles())
        # make the roles unique
        user_roles = dict(zip(user_roles, user_roles)).keys()

        # Set the local roles with the security of the inviter. If
        # he has no longer permissions on this context this will
        # fail.
        _old_security_manager = AccessControl.getSecurityManager()
        _new_user = self.context.acl_users.getUserById(
            self.invitation.inviter)
        AccessControl.SecurityManagement.newSecurityManager(
            self.request, _new_user)
        try:
            self.context.manage_setLocalRoles(self.member.getId(),
                                              user_roles)
            self.context.reindexObjectSecurity()
        except:
            AccessControl.SecurityManagement.setSecurityManager(
                _old_security_manager)
            raise
        else:
            AccessControl.SecurityManagement.setSecurityManager(
                _old_security_manager)

    def roles(self):
        """List of roles to give the `self.user` on the `self.context`.
        Reader ist default, and must be set.
        """
        registry = getUtility(IRegistry)
        config = registry.forInterface(IParticipationRegistry)

        if config.allow_multiple_roles:
            default_role = ['Reader', ]
        else:
            default_role = []

        if hasattr(self.invitation, 'roles'):
            return list(self.invitation.roles) + default_role
        return default_role
