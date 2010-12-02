from plone.principalsource import source
from plone.principalsource.term import PrincipalTerm


class ParticipationUsers(source.PrincipalSource):

    def _term_for_result(self, result_dict):
        id = result_dict['id']

        token = id
        if isinstance(token, unicode):
            token = token.encode('utf-8')

        type = result_dict.get('principal_type', 'user')
        value = result_dict.get('login', result_dict.get('groupid')) or id
        title = result_dict.get('title') or value

        # Attempt to get a title from the fullname if not set. Unfortunately,
        # source_users doesn't have fullname, and mutable_properties doesn't
        # match on login name or id when searching.

        if title == value:
            if type == 'user':
                user = self.acl_users.getUserById(id)
                if user is not None:
                    try:
                        # XXX: user.getProperty() is PlonePAS specfic
                        title = user.getProperty('fullname') or value
                        if user.getProperty('email'):
                            title += ' (%s)' % user.getProperty('email')
                    except AttributeError:
                        pass
        return PrincipalTerm(value=value, type=type, token=token, title=title)


class ParticipationBinder(source.PrincipalSourceBinder):

    def __call__(self, context):
        return ParticipationUsers(context, self.users, self.groups)


ParticipationUsersFactory = ParticipationBinder(users=True, groups=False)
