from utils import human_bytes
from Hubic.swift import SwiftContainers, SwiftClientWrapper
import logging
import config
logger = logging.getLogger("%s.%s"%(config.appname, __name__))


class AuthPackage(object):
    def __init__(self, username, password, hubic_client_id, hubic_client_secret):
        self.login = username
        self.password = password
        self.client_id = hubic_client_id
        self.client_secret = hubic_client_secret
        self.redirect_uri = "https://example.com/"
        self.timeout = 30
        self.OAUTH = "https://api.hubic.com/oauth/"
        self.HUBIC_API = "https://api.hubic.com/1.0/"



class Hubic(object):
    def __init__(self, auth_package = None):
        self._containers = None
        self.swift_client = SwiftClientWrapper(auth_package)

    @property
    def containers(self):
        if self._containers is None:
            self._containers = SwiftContainers(self.swift_client)
        return self._containers

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        account_info = self.swift_client.head_account()
        l1 = u"| # Objects : {0:^10} | # containers : {1:^4} | Quota : {2:>6}/{3:<6} ({4:^6}%)|".format(
            account_info['x-account-object-count'],
            account_info['x-account-container-count'],
            human_bytes(int(account_info['x-account-bytes-used'])),
            human_bytes(int(account_info['x-account-meta-quota'])),
            round(int(account_info['x-account-bytes-used']) * 100.0/ int(account_info['x-account-meta-quota']),2)
        )
        out = u"-"*len(l1)
        out += "\r\n"
        out += l1
        out += "\r\n"
        out += u"-"*len(l1)
        out += "\r\n"
        return out

    def upload(self, files):
        size = sum([f['bytes'] for f in files])
        logger.warning("%s will be uploaded"%(human_bytes(size)))
        hubic_files_container = self.containers['default']
        hubic_files_container.upload(files)
        logger.warning("Upload done")

    def createDirectory(self, path):
        hubic_files_container = self.containers['default']
        hubic_files_container.createDirectory(path)

    def getAllObjectsMetadataIndexedByPath(self, path=None, ignored_exts=None, prefix=None, limit=None):
        obj_dict = {}
        hubic_files_container = self.containers['default']
        if path[0] == "/":
            path = path[1:]
        if prefix[0] == "/":
            prefix = prefix[1:]
        hubic_files_container.filterBy(path=path, limit=limit)
        for object in hubic_files_container:
            name = object['name']
            ignore_file = False
            if ignored_exts is not None:
                for ign_ext in ignored_exts:
                    if name.endswith(ign_ext):
                        logger.debug("Ignoring %s (based on file extension)"%name)
                        ignore_file = True
                        continue
            if ignore_file:
                continue
            if prefix is not None:
                name = name.replace(prefix, "")
            obj_dict[name] = object
        objects = None
        return obj_dict




if __name__ == '__main__':

    import logging
    logging.basicConfig(level = logging.DEBUG)

    a = AuthPackage(
        username="", # Used to authenticate to the Oauth Page
        password="",
        hubic_client_id="", # ID of the app
        hubic_client_secret="", #PWD of the app
    )


    h=Hubic(a)

    print h

    print h.containers

    print h.containers[1]

    for o in h.containers:
        print o

    pass
