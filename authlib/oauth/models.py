from .. import interface

from .auth import Auth

class App(interface.App):
    key = None
    secret = None

    def auth(self, *args, **kwargs):
        return Auth(self, *args, **kwargs)

    def __unicode__(self):
        return 'oauth.App(%s)' % self.key


class Token(interface.Token):
    oauth_token = None
    oauth_token_secret = None

    @property
    def auth(self):
        return Auth(self.app, self)
