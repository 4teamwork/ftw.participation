ftw.participation
=================


With `ftw.participation` users can invite other users to a participate in
a area (e.g. Workspace) of a Plone installation.

A privileges user is able to invite another person by going to the invite view
and entering the e-mail address of the other person. The person receives a email
with a link to the Plone installation where he / she can log in with a existing
user or create a new one. On the invitations view he / she can now accept or
deny the invitation. When the invitation is accepted the user gets the configured
privileges on the context where he / she is invited.

The invitations are stored in a special container in the annotations of the
plone site root.

Each invitation has its own unique id, which is used in the URL sent to the
invited person. When the plone site is accessed using this link the invitation
is assigned to the users session. That's why he can accept the invitation although
he may be logged in with another user ID.


Activating
----------

First you need to import the generic setup profile, which adds some actions, a
browser layer and other stuff.

For activating the participation on a folderish content object give it the Interface
`ftw.participation.interfaces.IParticipationSupport` which enables the participation
on this context. This adds a new action "Manage participants" on this context and
you can invite other people.

A invited person will receive a e-mail containing a link to the platform,
containing the invitation id. After registering / logging in there is a new action
"My invitations" in the user menu, where the user can accept or reject the
invitation.


Using Quotas
------------

Providing the interface `ftw.participation.interfaces.IParticipationQuotaSupport`
adds a "Maximum amount of participaants" field to the schema which defines how
many other users can be invited.

When a quota is set the user can only invite that amount of user to this context. There
is a validator on the invitation form which ensures that the quota will not be crossed.

When setting the quota to `5` it is only possible to invite 4 other users because the
first participant is the owner, which usually already exists. Inviting the same user
multiple times counts also multiple times, but the invitor is able to retract the
invitation on the "My invitations" view.


Customizing email messages
--------------------------

If a person is invitied to a context he gets a e-mail notification. If this person accepts
or rejects the invitation the inviter is notified by e-mail. Those e-mails are multipart
emails containing a HTML part and a plaintext fallback part.

The messages may be customized eather by overwriting the translations or by customizing the
mail templates in `ftw.participation.browser`.


Installing
----------

- Just add ``ftw.participation`` to the eggs in your buildout configuration:

::

    [instance]
    eggs +=
        ftw.participation


- Install the generic setup profile.


Links
-----

- Main github project repository: https://github.com/4teamwork/ftw.participation
- Issue tracker: https://github.com/4teamwork/ftw.participation/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.participation
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.participation


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.participation`` is licensed under GNU General Public License, version 2.
