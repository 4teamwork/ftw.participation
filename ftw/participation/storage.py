from Products.CMFCore.utils import getToolByName
from datetime import datetime
from ftw.participation.interfaces import IInvitationStorage
from persistent.dict import PersistentDict
from persistent.list import PersistentList
from zope.annotation.interfaces import IAnnotations
from zope.component import adapts
from zope.interface import Interface
from zope.interface import implements
import AccessControl
from hashlib import md5


class InvitationStorage(object):
    """The invitation stores and manages the invitation. All modification in
    the list of invitations (appending new invitations, deleting existing
    invitations, etc.) should be done with through the invitation storage.

    The invitation storage is adapter adapting any context. The storage stores
    its data into annotations on the plone site root.
    """

    implements(IInvitationStorage)
    adapts(Interface)

    ANNOTATIONS_DATA_KEY = 'ftw.participation.storage : invitations'
    SESSION_PENDING_KEY = 'ftw.participation.storage : pending invitations'

    def __init__(self, context):
        """Adapts any context within a plone site
        """
        self.context = context
        portal_url = getToolByName(self.context, 'portal_url')
        self.portal = portal_url.getPortalObject()

    @property
    def portal_annotations(self):
        """The annotations of the plone site root
        """
        return IAnnotations(self.portal)

    @property
    def invitations(self):
        """A persistent dictionary of all invitations. The key is the email
        address of the invited user, the values are `PersistentList`s of
        `Invitations` of this user / email address.

        """
        cache_key = '_invitations_list'
        if cache_key not in dir(self):
            # didnt cache it yet, get it from the annotations (and cache it)
            if self.ANNOTATIONS_DATA_KEY not in self.portal_annotations:
                # dictionary does not exist in the annotations, create it
                self.portal_annotations[self.ANNOTATIONS_DATA_KEY] = \
                    PersistentDict()
            setattr(self, cache_key,
                    self.portal_annotations[self.ANNOTATIONS_DATA_KEY])
        return getattr(self, cache_key)

    def get_used_iids(self):
        """Returns a dict of all currently existing invitations with their id
        as key. This method is complex, do not use it often :)

        """
        data = {}
        for email, users_invitiations in self.invitations.items():
            for invitation in users_invitiations:
                data[invitation.iid] = invitation
        return data

    def generate_iid_for(self, invitation):
        """Generates a invitation id for the invitation and sets it (and
        returns it eventually).

        """
        used_iids = self.get_used_iids()
        # create a string as unique as possible, which will be hashed later
        # for that the info of the string are not decodable by the user
        base = '-'.join((
                str(datetime.now().isoformat()),
                invitation.email,
                invitation.inviter))
        counter = 1
        iid = None
        while not iid or iid in used_iids:
            iid = md5(base + str(counter)).hexdigest().strip()
            counter += 1
        # set the iid on the invitation
        invitation.iid = iid
        return iid

    def get_invitation_by_iid(self, iid, default=None):
        """Returns the invitation with the `iid` or `default` if there is none.
        """
        for users_invitiations in self.invitations.values():
            for invitation in users_invitiations:
                for invitation in users_invitiations:
                    if invitation.iid == iid:
                        return invitation
        return default

    def get_invitations_for_email(self, email=None, default=[]):
        """Returns a list of invitations for aspecific email address. If
        `email` is `None` the email is guessed by taking the email (or the
        userid) of the currently authenticated user. If there are no results,
        `default` is returend.
        """
        # guess the email if its `None`
        if email is None:
            mtool = getToolByName(self.context, 'portal_membership')
            member = mtool.getAuthenticatedMember()
            email = member.getProperty('email', member.getId())
        # move session-invitations - if necessary
        self.assign_pending_session_invitations()
        # the email is the key of the invitations data dict
        if email in self.invitations:
            return self.invitations.get(email)
        else:
            return default

    def get_invitations_invited_by(self, userid=None, default=[]):
        """Returns a list of invitations which are created by a specific user
        for any email address. If `userid` is `None` the userid of the
        authenticated member is taken. If therer are no results, `default`
        is returned.
        """
        # guess the `userid` if its `None`
        if userid is None:
            mtool = getToolByName(self.context, 'portal_membership')
            member = mtool.getAuthenticatedMember()
            userid = member.getId()
        # find all inivitations where the inviter is `userid`
        list_ = []
        for users_invitiations in self.invitations.values():
            for inv in users_invitiations:
                if inv.inviter == userid:
                    list_.append(inv)
        return list_ or default

    def get_invitations_for_context(self, context, default=[]):
        """Returns all invitations for a context. This method may be slow.
        """
        list_ = []
        for users_invitiations in self.invitations.values():
            for inv in users_invitiations:
                if inv.get_target() == context:
                    list_.append(inv)
        return list_ or default

    def get_pending_session_invitations(self, default=[]):
        """When the user clicks on the invitation in the email program the
        invitation is temporary stored in the session too (if the user is
        not logged in). In some situations (e.g. after registrering or logging
        in) the invitation (from the session) is moved to the user which the
        user is now logged in.
        This covers some special use cases, when as example the user does not
        use the email address, to which the invitation is sent for the user
        of the plone site. That's how invitations are reassigned to other
        users.

        This method returns a list of the current session-invitations or
        `default` if there is no list.
        """
        session = self.context.REQUEST.SESSION
        return session.get(self.SESSION_PENDING_KEY, default)

    def set_invitation_pending_for_session(self, invitation):
        """Sets the `invitation` as pending in the session.
        See the docstring of get_pending_session_invitations for further
        details.

        """
        session = self.context.REQUEST.SESSION
        if self.SESSION_PENDING_KEY not in session.keys():
            session[self.SESSION_PENDING_KEY] = PersistentList()
        session[self.SESSION_PENDING_KEY].append(invitation.iid)

    def assign_pending_session_invitations(self, email=None):
        """
        This method reassigns the session-invitations to the `email` (or the
        authenticated user if `email` is `None`) and removes them from the
        session.

        See the docstring of get_pending_session_invitations for futher
        details.
        """
        # guess the email, if it's not defined
        if email is None:
            mtool = getToolByName(self.context, 'portal_membership')
            member = mtool.getAuthenticatedMember()
            if member == AccessControl.SpecialUsers.nobody:
                # the user is not logged in and the `email` is not defined, so
                # we do not know to whom whe should assign the invitations
                return False
            # use the email (or - if not defined - the userd)
            email = member.getProperty('email', member.getId())
        # get the pending invitations from the session
        pending_invitations = self.get_pending_session_invitations()
        if pending_invitations and len(pending_invitations):
            for iid in pending_invitations[:]:
                inv = self.get_invitation_by_iid(iid)
                if inv:
                    self.reassign_invitation(inv, email)
            # remove the list from the session - all session-invitations are
            # dropped from the session
            del self.context.REQUEST.SESSION[self.SESSION_PENDING_KEY]

    def add_invitation(self, invitation):
        """Adds a invitation object to the storage.
        """
        # the key of the invitations dict is `invitaiton.email`, the value
        # is a `PersistentDict`
        if invitation.email not in self.invitations:
            self.invitations[invitation.email] = PersistentList()
        # check if its already added
        if invitation in self.invitations[invitation.email]:
            return False
        else:
            self.invitations[invitation.email].append(invitation)

    def remove_invitation(self, invitation):
        """Removes the `invitation` from the storage and destroys it
        """
        if invitation.email in self.invitations and \
                invitation in self.invitations[invitation.email]:
            # if the invitation is stored under invitation.email remove
            # it from there...
            self.invitations[invitation.email].remove(invitation)
            if len(self.invitations[invitation.email]) == 0:
                del self.invitations[invitation.email]
            return True
        else:
            # ... otherwise search it
            for email, users_invitiations in self.invitations.items():
                if invitation in users_invitiations:
                    users_invitiations.remove(invitation)
                    if len(users_invitiations) == 0:
                        del self.invitations[email]
                    return True
        return False

    def reassign_invitation(self, invitation, new_email):
        """Reassigns a invitation to another email address (`new_email`).
        """
        # remove invitation from storage
        self.remove_invitation(invitation)
        # change the email
        invitation.email = new_email
        # re-add it to the storage
        self.add_invitation(invitation)
