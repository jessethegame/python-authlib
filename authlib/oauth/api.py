import callm

from .errors import Error
from . import utils

#TODO: detailed error messages
#TODO: GET or POST?
class API(callm.Connection):
    request_token_path = None
    access_token_path = None
    authorize_uri = None
    authenticate_uri = None

    def get_request_token(self):
        response = self.POST(self.request_token_path)
        if response.status != 200:
            raise Error('Invalid response while obtaining request token.')
        return response.query

    def get_access_token(self, oauth_token, oauth_token_secret, oauth_verifier):
        class _Token: pass
        token = _Token()
        token.oauth_token = oauth_token
        token.oauth_token_secret = oauth_token_secret
        self.token = token
        body = 'oauth_verifier=' + utils.percent_encode(oauth_verifier)
        response = self.POST(self.access_token_path, body=body)
        if response.status != 200:
            raise Error('Invalid response while obtaining access token.')
        query = response.query
        token = dict((k, query.pop(k)) for k in (
                'oauth_token', 'oauth_token_secret'))
        return token, query

    # TODO: If one is missing, use the other
    def get_authenticate_url(self, **kwargs):
        return callm.URL(self.authenticate_uri, **kwargs)

    def get_authorize_url(self, **kwargs):
        return callm.URL(self.authorize_uri, **kwargs)


