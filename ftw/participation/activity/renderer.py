from ftw.activity.browser.renderer import DefaultRenderer
from zope.component.hooks import getSite
from ftw.participation import _
from ftw.participation.activity.utils import translate_and_join_roles
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class InvitationRenderer(DefaultRenderer):
    index = ViewPageTemplateFile('templates/invitation.pt')

    def position(self):
        return 900

    def match(self, activity, obj):
        return activity.attrs['action'].startswith('participation:')

    def render(self, activity, obj):
        return self.index(activity=activity,
                          obj=obj,
                          comment=self.prepare_comment(activity, obj))

    def prepare_comment(self, activity, obj):
        action = activity.attrs['action']
        actor_info = activity.get_actor_info()
        actor_fullname = actor_info.get('fullname').decode('utf-8')

        if action == 'participation:invitation_created':
            actor_email = activity.attrs['invitation:email'].decode('utf-8')
            roles = translate_and_join_roles(
                activity.attrs['invitation:roles'], obj, self.request)

            return _(u'activity_invitation_created_body',
                     default=u'${inviter} has invited ${mail} as ${roles}.',
                     mapping={'inviter': actor_fullname,
                              'mail': actor_email,
                              'roles': roles})

        if action == 'participation:invitation_retracted':
            actor_email = activity.attrs['invitation:email'].decode('utf-8')
            roles = translate_and_join_roles(
                activity.attrs['invitation:roles'], obj, self.request)

            return _(u'activity_invitation_retracted_body',
                     default=u'${actor} has retracted the invitation'
                     u' for ${mail}.',
                     mapping={'actor': actor_fullname,
                              'mail': actor_email})

        if action == 'participation:role_changed':
            subject_fullname = self.get_fullname_of(
                activity.attrs['roles:userid'])
            removed_roles = translate_and_join_roles(
                activity.attrs['roles:removed'], obj, self.request)
            added_roles = translate_and_join_roles(
                activity.attrs['roles:added'], obj, self.request)

            return _(u'activity_role_changed_body',
                     default=u'${actor} has changed the role of ${subject}'
                     u' from ${removed_roles} to ${added_roles}.',
                     mapping={'actor': actor_fullname,
                              'subject': subject_fullname,
                              'removed_roles': removed_roles,
                              'added_roles': added_roles})

        if action == 'participation:role_removed':
            subject_fullname = self.get_fullname_of(
                activity.attrs['roles:userid'])

            return _(u'activity_participant_removed_body',
                     default=u'${actor} has removed the'
                     u' participant ${subject}.',
                     mapping={'actor': actor_fullname,
                              'subject': subject_fullname})

        return None

    def get_fullname_of(self, userid):
        membership = getToolByName(getSite(), 'portal_membership')
        member = membership.getMemberById(userid)
        if not member:
            result = userid or 'N/A'
        else:
            result = member.getProperty('fullname') or userid

        if not isinstance(result, unicode):
            result = result.decode('utf-8')

        return result
