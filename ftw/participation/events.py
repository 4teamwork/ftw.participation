from ftw.participation.interfaces import IInvitationAcceptedEvent
from ftw.participation.interfaces import IInvitationCreatedEvent
from ftw.participation.interfaces import IInvitationEvent
from ftw.participation.interfaces import IInvitationRejectedEvent
from ftw.participation.interfaces import IInvitationRetractedEvent
from ftw.participation.interfaces import ILocalRoleRemoved
from ftw.participation.interfaces import IRolesChangedEvent
from zope.component.interfaces import ObjectEvent
from zope.interface import implements


class InvitationEvent(ObjectEvent):
    """An event related to an invitation.
    """
    implements(IInvitationEvent)

    def __init__(self, object, invitation):
        self.object = object
        self.invitation = invitation


class InvitationCreatedEvent(InvitationEvent):
    """An invitation was created.
    """
    implements(IInvitationCreatedEvent)

    def __init__(self, object, invitation, comment):
        self.object = object
        self.invitation = invitation
        self.comment = comment


class InvitationAcceptedEvent(InvitationEvent):
    """An invitation was accepted.
    """
    implements(IInvitationAcceptedEvent)


class InvitationRejectedEvent(InvitationEvent):
    """An invitation was rejected.
    """
    implements(IInvitationRejectedEvent)


class InvitationRetractedEvent(InvitationEvent):
    """An invitation was retracted.
    """
    implements(IInvitationRetractedEvent)


class RolesChangedEvent(object):
    """The roles of a participant was changed.
    """
    implements(IRolesChangedEvent)

    def __init__(self, object, userid, old_roles, new_roles):
        self.object = object
        self.userid = userid
        self.old_roles = old_roles
        self.new_roles = new_roles


class LocalRoleRemoved(object):
    implements(ILocalRoleRemoved)

    def __init__(self, object, userid):
        self.object = object
        self.userid = userid
