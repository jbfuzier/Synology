import logging
import config
import re
import urlparse
import json
from datetime import datetime, timedelta
import http

logger = logging.getLogger("%s.%s"%(config.appname, __name__))

class RequestTokenManager(object):

    def __init__(self, auth_package):
        self.auth_package = auth_package
        self._token = None

    @property
    def token(self):
        if self._token is None:
            logging.debug("Requesting oauth request token (should appen only once")
            self._requestRequestToken()
            logging.debug("\t oauth request token : %s"%self._token)
            #TODO : drop user & password
        return self._token

    def _requestRequestToken(self):
        oauth_id = self.__step1_check_app_valid_and_get_oauthid()
        self.__step2_get_oauth_request_token(oauth_id)

    def __step1_check_app_valid_and_get_oauthid(self):
        c, r = http._get(
            self.auth_package.OAUTH+'auth/',
            {
                'client_id': self.auth_package.client_id,
                'redirect_uri': self.auth_package.redirect_uri,
                'scope': 'credentials.r,account.r',
                'response_type': 'code',
                'state': ''
            }
        )
        if r.status != 200:
            raise Exception("Incorrect/unauthorized "
                            "HubiC client_id (%s)"%str(http._parse_error(r)))
        rdata = r.read()
        c.close()
        try:
            from lxml import html as lxml_html
        except ImportError:
            lxml_html = None

        if lxml_html:
            oauth = lxml_html.document_fromstring(rdata).xpath('//input[@name="oauth"]')
            oauth = oauth[0].value if oauth else None
        else:
            oauth = re.search(r'<input\s+[^>]*name=[\'"]?oauth[\'"]?\s+[^>]*value=[\'"]?(\d+)[\'"]?>', rdata)
            oauth = oauth.group(1) if oauth else None

        if not oauth:
            raise Exception("Unable to get oauth_id from authorization page")
        return oauth


    def __step2_get_oauth_request_token(self, oauth_id):
        """
            Use the user login & password to get an oauth request token (required only once)
        """

        c, r = http._post(
            self.auth_package.OAUTH+'auth/',
            data={
                'action': 'accepted',
                'oauth': oauth_id,
                'login': self.auth_package.login,
                'user_pwd': self.auth_package.password,
                'account': 'r',
                'credentials': 'r',

                },
        )
        data = r.read()
        c.close()

        if r.status == 302:
            location = r.getheader('location', '')
            if not location.startswith(self.auth_package.redirect_uri):
                raise Exception("Got an unexpected redirection to %s"%location)
            query = urlparse.urlsplit(location).query
            query_dict = dict(urlparse.parse_qsl(query))
            if 'code' in query_dict:
                self._token = query_dict['code'] # Oauth Request Token
        else:
            raise Exception("Got unexpected http code %s (%s)" % (r.status, r.reason))

class AccessTokenManager(object):
    def __init__(self, auth_package):
        self.auth_package = auth_package
        self.requestTokenManager = RequestTokenManager(auth_package)
        self._token = None
        self._refresh_token = None
        self._expire = None

    @property
    def token(self):
        if self._token is None:
            self._requestAccessToken()
        elif self.expired:
            self._renewAccessToken()
        logger.debug("Requested oauth access token\t token : %s - expires : %s"%(self._token, self._expire))
        return self._token

    def _renewAccessToken(self):
        self._requestAccessToken()

    @property
    def expired(self):
        return datetime.now() > self._expire

    def _requestAccessToken(self):
        oauth_request_token = self.requestTokenManager.token

        c, r = http._post(
            self.auth_package.OAUTH+'token/',
            {
                'code': oauth_request_token,
                'redirect_uri': self.auth_package.redirect_uri,
                'grant_type': 'authorization_code',
                },
            {
                'Authorization': 'Basic '+('{0}:{1}'.format(self.auth_package.client_id, self.auth_package.client_secret)
                                           .encode('base64').replace('\n', ''))
            }
        )

        rdata = r.read()
        c.close()

        if r.status != 200:
            try:
                err = json.loads(rdata)
                err['code'] = r.status
            except Exception as e:
                err = {}

            raise Exception("Unable to get oauth access token, "
                            "wrong client_id or client_secret ? (%s)"%str(err))

        oauth_token = json.loads(rdata)
        if oauth_token['token_type'].lower() != 'bearer':
            raise Exception("Unsupported access token type")
        self._token = oauth_token['access_token']
        self._refresh_token = oauth_token['refresh_token']
        self._expire = datetime.now() + timedelta(seconds = oauth_token['expires_in'] - 10)

class SwiftTokenManager(object):
    def __init__(self, auth_package):
        self.auth_package = auth_package
        self._token = None
        self._expire = None
        self._endpoint = None
        self.accessTokenManager = AccessTokenManager(auth_package)

    @property
    def endpoint(self):
        a = self.token # Force to get information
        return self._endpoint

    @property
    def token(self):
        if self._token is None:
            self._requestSwiftToken()
        elif self.expired:
            self._renewSwiftToken()
        logger.debug("Requested SWIFT ticket\t token : %s - expires : %s - endpoint : %s"%(self._token, self._expire, self._endpoint))
        return self._token

    def _renewSwiftToken(self):
        self._requestSwiftToken()

    def _requestSwiftToken(self):
        """
        Request a swift token by creating an accesstoken
        """
        oauth_access_token = self.accessTokenManager.token
        c, r = http._get(
            self.auth_package.HUBIC_API+'account/credentials/',
            headers={
                'Authorization': 'Bearer '+oauth_access_token
            }
        )
        result = json.loads(r.read())
        c.close()

        if r.status != 200:
            try:
                err =result
                err['code'] = r.status
            except Exception as e:
                err = {}

            raise Exception("Unable to get swift token, "
                            "(%s)"%str(err))

        self._endpoint = result['endpoint']
        self._token = result['token']
        self._expire = datetime.strptime( result['expires'][:-6], "%Y-%m-%dT%H:%M:%S" ) - timedelta(seconds=10)
    @property
    def expired(self):
        return datetime.now() > self._expire
