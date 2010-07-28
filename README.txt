
Introduction
============


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
