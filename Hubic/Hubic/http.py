from httplib  import HTTPSConnection
from urllib   import urlencode
import urlparse
import re
import time
import config
import logging

logger = logging.getLogger("%s.%s"%(config.appname, __name__))

def parse_url(url):
    """
    Given a URL, returns a 4-tuple containing the hostname, port,
    a path relative to root (if any), and a boolean representing
    whether the connection should use SSL or not.
    """
    (scheme, netloc, path, params, query, frag) = urlparse.urlparse(url)

    # We only support web services
    if not scheme in ('http', 'https'):
        raise Exception('Scheme must be one of http or https')

    is_ssl = scheme == 'https' and True or False

    # Verify hostnames are valid and parse a port spec (if any)
    match = re.match('([a-zA-Z0-9\-\.]+):?([0-9]{2,5})?', netloc)

    if match:
        (host, port) = match.groups()
        if not port:
            port = is_ssl and '443' or '80'
    else:
        raise Exception('Invalid host and/or port: %s' % netloc)

    return (host, int(port), path.strip('/'), is_ssl)


def _parse_error( resp):
    headers = dict(resp.getheaders())
    if not 'location' in headers:
        return None
    query = urlparse.urlsplit(headers['location']).query
    qs = dict(urlparse.parse_qsl(query))
    return {'error': qs['error'], 'error_description': qs['error_description']}


def _get(url, params=None, headers={}):
    return _http_request(url, params, headers, method='GET')




def _post(url, data=None, headers={}):
    return _http_request(url, data, headers, method='POST')

def _http_request(url, params=None, headers={}, method='GET'):
    host, port, uri, is_ssl = parse_url(url)
    conn = HTTPSConnection(host, port, timeout=config.timeout)
    for i in range(config.retry):
        try:
            if method == 'GET':
                conn.request('GET', '/' + uri + ('?'+urlencode(params) if params else ''),
                    headers=headers)
            elif method == 'POST':
                data = params
                headers.update({'Content-type': 'application/x-www-form-urlencoded'})
                conn.request('POST', '/' + uri, urlencode(data) if data else None, headers)
            response = conn.getresponse()
            if str(response.status)[0]=="5":
                logger.error("http error %s"%response)
                raise Exception
            return conn, response
        except Exception as e:
            backoff = config.backoff * config.retry
            logger.debug("Got Exception %s while %sing %s, waiting %s before retry..."%(e, method, url, backoff))
            time.sleep(backoff)



