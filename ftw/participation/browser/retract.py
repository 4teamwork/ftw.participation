from ftw.participation import _
from ftw.participation.browser.accept import AcceptInvitation
from ftw.participation.events import InvitationRetractedEvent
from ftw.participation.interfaces import IInvitationStorage
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from zExceptions import Redirect
from zope.event import notify
import os.path


class RetractInvitation(AcceptInvitation):
    """The inviter retracts the invitation.
    """

    def __call__(self, iid=None):
        if not iid:
            iid = self.request.get('iid')

        self.load(iid)
        notify(InvitationRetractedEvent(self.target, self.invitation))

        msg = _(u'info_invitation_retracted',
                default=u'You have retracted the invitation.')
        IStatusMessage(self.request).addStatusMessage(msg)

        # destroy the invitation
        self.storage.remove_invitation(self.invitation)
        del self.invitation

        # redirect back
        url = self.request.get('HTTP_REFERER',
                               os.path.join(self.context.portal_url(),
                                            '@@invitations'))
        return self.request.RESPONSE.redirect(url)

    def load(self, iid):
        """Loads storage, invitation, target, etc
        """
        self.storage = IInvitationStorage(self.context)
        self.invitation = self.storage.get_invitation_by_iid(iid)
        self.target = self.invitation.get_target()

        # sanity check
        mtool = getToolByName(self.context, 'portal_membership')
        self.member = mtool.getAuthenticatedMember()
        if not self.invitation \
                or self.invitation.inviter != self.member.getId():
            msg = _(u'error_invitation_not_found',
                    default=u'Could not find the invitation.')
            IStatusMessage(self.request).addStatusMessage(msg, type='error')
            raise Redirect(self.context.portal_url())
