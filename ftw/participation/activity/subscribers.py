from ftw.activity.catalog import get_activity_soup
from ftw.activity.catalog.record import ActivityRecord


def create_record_from_invitation(obj, invitation, action,
                                  actor_userid=None, date=None):
    record = ActivityRecord(obj, action,
                            actor_userid=actor_userid, date=date)
    record.attrs['invitation:inviter'] = invitation.inviter
    record.attrs['invitation:email'] = invitation.email
    record.attrs['invitation:roles'] = tuple(invitation.roles)
    return record


def invitation_created(obj, event, actor_userid=None, date=None):
    record = create_record_from_invitation(
        obj, event.invitation, 'participation:invitation_created')
    record.attrs['invitation:comment'] = event.comment
    return get_activity_soup().add(record)


def invitation_accepted(obj, event, actor_userid=None, date=None):
    record = create_record_from_invitation(
        obj, event.invitation, 'participation:invitation_accepted')
    return get_activity_soup().add(record)


def invitation_rejected(obj, event, actor_userid=None, date=None):
    record = create_record_from_invitation(
        obj, event.invitation, 'participation:invitation_rejected')
    return get_activity_soup().add(record)


def invitation_retracted(obj, event, actor_userid=None, date=None):
    record = create_record_from_invitation(
        obj, event.invitation, 'participation:invitation_retracted')
    return get_activity_soup().add(record)


def role_changed(obj, event, actor_userid=None, date=None):
    record = ActivityRecord(obj, 'participation:role_changed',
                            actor_userid=actor_userid, date=date)
    record.attrs['roles:userid'] = event.userid
    record.attrs['roles:old'] = tuple(event.old_roles)
    record.attrs['roles:new'] = tuple(event.new_roles)
    record.attrs['roles:removed'] = tuple(
        set(event.old_roles) - set(event.new_roles))
    record.attrs['roles:added'] = tuple(
        set(event.new_roles) - set(event.old_roles))
    return get_activity_soup().add(record)


def role_removed(obj, event, actor_userid=None, date=None):
    record = ActivityRecord(obj, 'participation:role_removed',
                            actor_userid=actor_userid, date=date)
    record.attrs['roles:userid'] = event.userid
    return get_activity_soup().add(record)
