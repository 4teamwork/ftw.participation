from AccessControl import SpecialUsers
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.statusmessages.interfaces import IStatusMessage
from ftw.participation import _
from ftw.participation.interfaces import IInvitationStorage
from zExceptions import Forbidden
import os.path


class InvitationsView(BrowserView):
    """The invitations shows a listing of invitations the user got (where he
    was invited by another user) and a listing of invitations where he invited
    someone else.

    """

    template = ViewPageTemplateFile('invitations.pt')

    def __call__(self):
        self.storage = IInvitationStorage(self.context)
        self.handle_pending_invitations()
        authenticator = self.context.restrictedTraverse('@@authenticator',
                                                        None)
        if not self.is_logged_in():
            # redirect to home when no
            pending_iids = self.storage.get_pending_session_invitations()
            if not len(pending_iids):
                # no pending sessions and not logged in -> go to home
                url = self.context.portal_url()
                return self.request.RESPONSE.redirect(url)

            else:
                # check if the email of at least one pending invitation is
                # already used by any user -> then the current user may be
                # this user, so we redirect to the login form
                passearch = self.context.unrestrictedTraverse('@@pas_search')
                for iid in pending_iids:
                    invitation = self.storage.get_invitation_by_iid(iid)
                    if not invitation:
                        # Maybe a deleted Invitation is still in the session.
                        continue
                    if len(passearch.searchUsers(email=invitation.email)) > 0:
                        url = os.path.join(
                            self.context.portal_url(),
                            'login_form?came_from=@@invitations')
                        return self.request.RESPONSE.redirect(url)
                # if we cannot find it we redirect to the invite_join_form
                url = os.path.join(self.context.portal_url(),
                                   'welcome_invited')
                # store one of the email addresses to the session. it can be
                # used later while registering as proposal
                if invitation:
                    self.request.SESSION['invite_email'] = invitation.email
                return self.request.RESPONSE.redirect(url)

        # not logged in -> show the view...
        else:
            # if we have pending session invitations, we should assign them to
            # the current user now.
            self.storage.assign_pending_session_invitations()
            if self.request.get('form.submitted', False):
                # sanity check with authenticator
                if not authenticator.verify():
                    raise Forbidden

                # handle accepted invitations
                if self.request.get('accept', False):
                    for iid in self.request.get('received_invitations', []):
                        self.context.unrestrictedTraverse(
                            '@@accept_invitation')(iid)

                # handle rejected invitations
                if self.request.get('reject', False):
                    for iid in self.request.get('received_invitations', []):
                        self.context.unrestrictedTraverse(
                            '@@reject_invitation')(iid)

                # hande reetracted invitations
                if self.request.get('retract', False):
                    for iid in self.request.get('sent_invitations', []):
                        self.context.unrestrictedTraverse(
                            '@@retract_invitation')(iid)

        return self.template()

    def get_received_invitations(self):
        """Returns all invitations which the user has received and open.
        """
        return self.storage.get_invitations_for_email()

    def get_sent_invitations(self):
        """Returns all open invitations created by the current user.
        """
        return self.storage.get_invitations_invited_by()

    def handle_pending_invitations(self):
        """When the `iid` of a invitation is in the request
        (@@invitaitons?iid=bla) and the user is not authenticated, we mark this
        invitation in the session. If there is a `iid` but the user is
        authenticated we can reassign the invitation to this user.

        """
        iid = self.request.get('iid', False)
        if not iid:
            return
        invitation = self.storage.get_invitation_by_iid(iid)
        if not invitation:
            # the invitation is expired or answered
            msg = _(u'warning_invitaiton_expired',
                    default=u'The invitation has expired.')
            IStatusMessage(self.request).addStatusMessage(msg, type='warning')
            return

        if self.is_logged_in():
            # reassign to current user
            mtool = getToolByName(self.context, 'portal_membership')
            member = mtool.getAuthenticatedMember()
            new_email = member.getProperty('email', False) or member.getId()
            self.storage.reassign_invitation(invitation, new_email)
        else:
            # set pending for session
            self.storage.set_invitation_pending_for_session(invitation)

    def is_logged_in(self):
        """Returns wheather the user is logged in or not.
        """
        mtool = getToolByName(self.context, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        return member != SpecialUsers.nobody
