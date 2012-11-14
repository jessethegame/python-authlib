import time
import random
import hmac
import hashlib
import base64
import urlparse
import urllib

from .. import interface


def _utf8_str(s):
    """Convert unicode to utf-8."""
    if isinstance(s, unicode):
        return s.encode("utf-8")
    else:
        return str(s)

def percent_encode(s):
    return urllib.quote(_utf8_str(s), '~')

def percent_encode_dict(d):
    return dict(map(percent_encode, tup) for tup in d.iteritems())

def normalize_url(url):
    scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)

    # Exclude default port numbers.
    if scheme == 'http' and netloc[-3:] == ':80':
        netloc = netloc[:-3]
    elif scheme == 'https' and netloc[-4:] == ':443':
        netloc = netloc[:-4]
    if scheme not in ('http', 'https'):
        raise ValueError("Unsupported URL %s (%s)." % (url, scheme))

    # Normalized URL excludes params, query, and fragment.
    return urlparse.urlunparse((scheme, netloc, path, None, None, None))

def build_base_string(method, url, parameter_string):
    # Prepare url by stripping fragments and query string
    base_url = normalize_url(url)
    return '&'.join((
            method.upper(),
            percent_encode(base_url),
            percent_encode(parameter_string)))

def build_header(header):
    return 'OAuth ' + ', '.join(('='.join
        ((percent_encode(k), '"%s"' % percent_encode(v)))
        for k, v in sorted(header.iteritems())))

class Auth(interface.Auth):
    """
    An OAuth authorizer.
    """
    @property
    def signing_key(self):
        #TODO: sometime do this without +
        key = percent_encode(self.app.secret) + '&'
        if self.token:
            key += percent_encode(self.token.oauth_token_secret)
        return key

    def build_signature(self, msg):
        """Builds a hmac_sha1 hash for the message."""
        key = self.signing_key.encode('ascii')
        raw = msg.encode('ascii')
        mac = hmac.new(key, raw, hashlib.sha1)
        dig = mac.digest()
        sig = base64.b64encode(dig)
        return sig

    def oauth_header(self, method, uri, **other_params):
        header = {}

        # Add the basic oauth paramters
        header['oauth_consumer_key'] = self.app.key
        header['oauth_signature_method'] = 'HMAC-SHA1'
        header['oauth_version'] = '1.0'
        header['oauth_timestamp'] = int(time.time())
        header['oauth_nonce'] = random.getrandbits(64)

        # Add token if we're authorizing a user
        if self.token:
            header['oauth_token'] = self.token.oauth_token

        # Override default header and add additional header params
        header.update(self.options)

        #XXX: Sorting should be done prior to encoding!
        #XXX: Is that so?

        # Prepare the parameter string for the base string
        params_dict = header.copy()
        params_dict.update(other_params)
        params_string = urllib.urlencode(sorted(params_dict.iteritems()))

        # Build the base string from prepared parameter string
        base_string = build_base_string(method, uri, params_string)

        # Build the signature and add it to the parameters
        signature = self.build_signature(base_string)
        header['oauth_signature'] = signature

        # Return the constructed authorization header
        return build_header(header)

    def __call__(self, method, uri, body=None, headers={}):
        """
        Encode and sign a request according to OAuth 1.0 spec.

        Heads up!

        Does not support duplicate keys.
        """
        # Split the uri for the query string parameters
        parts = urlparse.urlsplit(uri)
        query_params = urlparse.parse_qsl(parts.query)
        body_params = urlparse.parse_qsl(body or '')

        other_params = {}
        other_params.update(dict(query_params))
        other_params.update(dict(body_params))

        headers['Authorization'] = self.oauth_header(method, uri, **other_params)

        body = urllib.urlencode(body_params)
        uri = urlparse.urlunsplit((parts.scheme,
                                   parts.netloc,
                                   parts.path,
                                   urllib.urlencode(query_params),
                                   parts.fragment))

        return method, uri, body, headers

