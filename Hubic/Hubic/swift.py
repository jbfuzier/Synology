import logging
from utils import human_bytes
import swiftclient
import config
import os
from Hubic.auth import SwiftTokenManager
logger = logging.getLogger("%s.%s"%(config.appname, __name__))


class SwiftObjects(object):
    created_directories = set()
    def __init__(self, swift_client, container, path = None, limit = None):
        self.swift_client = swift_client
        self.objects = None
        self.container = container
        self.path = path
        self.limit = limit
        if limit is None:
            self.full_listing = True

    def filterBy(self, path=None, limit=None):
        self.path = path
        self.limit = limit
        if limit is None:
            self.full_listing = True

    def createDirectory(self, path):
        # Create pseudo directory to make hubic happy
        if len(path) == 0:
            return
        if path in self.created_directories:
            logger.debug("Directory %s already exists"%path)
            return
        try:
            self.swift_client.put_object(
                container=self.container,
                obj=path,
                content_length = 0,
                contents = None,
                content_type = 'application/directory')
            logger.debug("Directory %s created"%path)
            self.created_directories.add(path)
        except swiftclient.ClientException as e:
            logger.warning("Failed to create pseudo dir %s on hubic : %s"%(path, e))

    def upload(self, to_upload):
        uploaded = 1
        dirs_to_create = [e for e in to_upload if e['is_dir']]
        files_to_upload = [e for e in to_upload if not e['is_dir']]
        """
        In swift objects are stored with an uri based name, there are no directories, BUT hubic only shows content if pseudo directories are created (empty file with content type directory)
        Even if objects are not shown in hubic due to a lack of pseudo dir, objects still exists
        """
        for dir_ in dirs_to_create:
            if dir_["name"][0] == "/": # Swift client (or hubic?) lib does not handle properly name starting with / (-> test.com/container//object)
                dir_["name"] = dir_["name"][1:]
            if len(dir_["name"])>1024:
                logger.error("dir %s name is too long (>1024)"%(dir_["name"])) #Swift object names are limited to 1024
            self.createDirectory(dir_['name'])

        for file_to_upload in files_to_upload:
            if file_to_upload["name"][0] == "/": # Swift client (or hubic?) lib does not handle properly name starting with / (-> test.com/container//object)
                file_to_upload["name"] = file_to_upload["name"][1:]
            if len(file_to_upload["name"])>1024:
                logger.error("filename %s is too long (>1024)"%(file_to_upload["name"])) #Swift object names are limited to 1024
            logger.info("Uploading %s (%s)- (%s/%s)"%(
                file_to_upload["name"],
                human_bytes(file_to_upload['bytes']),
                uploaded,
                len(files_to_upload)
                )
            )

            with open(file_to_upload['local_path']) as f:
                response_dict = {}
                try:
                    self.swift_client.put_object(
                        container = self.container,
                        obj = file_to_upload['name'],
                        contents=f,
                        content_length=file_to_upload['bytes'],
                        response_dict = response_dict,
                        etag=file_to_upload['hash']
                    )
                except swiftclient.ClientException as e:
                    logger.error("While storing %s : %s"%(e))
            try:
                stored_obj_attributes = self.swift_client.head_object(self.container, file_to_upload['name'])
                if (response_dict['headers']['etag'] != file_to_upload['hash']) or (stored_obj_attributes['etag'] != file_to_upload['hash']):
                    logger.critical("File %s got corrupted during upload"%(file_to_upload))
            except swiftclient.ClientException as e:
                logger.error("While storing %s : %s"%(e))
                if e.http_status == 404:
                    logger.error("File was not stored properly on hubic (404)")
            logger.debug("File %s stored sucessfully on hubic"%(file_to_upload))
            uploaded += 1
    #{'status': 201, 'headers': {'content-length': '0', 'last-modified': 'Mon, 04 Aug 2014 11:01:44 GMT', 'connection': 'close', 'etag': '5d933eef19aee7da192608de61b6c23d', 'x-trans-id': 'tx3cca9f2ab97a4d6e8c2b6d58afbcd10f', 'date': 'Mon, 04 Aug 2014 11:01:45 GMT', 'content-type': 'text/html; charset=UTF-8'}, 'reason': 'Created', 'response_dicts': [{'status': 201, 'headers': {'content-length': '0', 'last-modified': 'Mon, 04 Aug 2014 11:01:44 GMT', 'connection': 'close', 'etag': '5d933eef19aee7da192608de61b6c23d', 'x-trans-id': 'tx3cca9f2ab97a4d6e8c2b6d58afbcd10f', 'date': 'Mon, 04 Aug 2014 11:01:45 GMT', 'content-type': 'text/html; charset=UTF-8'}, 'reason': 'Created'}]}


    def refresh(self):
        logger.info("Fetching objects list for container %s"%self.container)
        self.objects = self.swift_client.get_container(
                        self.container,
                        full_listing = self.full_listing,
                        path = self.path,
                        limit=self.limit,
        )[1]
        logger.info("done : %s objects fetched"%len(self.objects))

    def __len__(self):
        if self.objects is None:
            self.refresh()
        return len(self.objects)

    def __iter__(self):
        if self.objects is None:
            self.refresh()
        for o in self.objects:
            yield o

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        if self.objects is None:
            self.refresh()
        out = u""
        out += u"|{0:^200}|{4:^10}|{1:^34}|{2:^28}|{3:^40}|\r\n".format(
            "Name",
            "Hash",
            "Last modified",
            "Content_type",
            "Size",
        )
        for object in self.objects:
            out += u"|{0:<200}|{4:^10}|{1:^34}|{2:<28}|{3:^40}|\r\n".format(
                object['name'],
                object['hash'],
                object['last_modified'],
                object['content_type'],
                human_bytes(int(object['bytes']))
            )
        return out


class SwiftContainers(object):
    def __init__(self, swift_client):
        self.swift_client = swift_client
        self.refresh()

    def refresh(self):
        logger.debug("Fetching containers list")
        self.containers = self.swift_client.get_account(full_listing = True)[1]
        pass

    def __len__(self):
        return len(self.containers)

    def __iter__(self):
        for c in self.containers:
            yield SwiftObjects(self.swift_client, c['name'])

    def __getitem__(self, item):
        if type(item) is int:
            name = self.containers[item]['name']
        elif type(item) in [str, unicode]:
            name = item
        else:
            return None
        return SwiftObjects(self.swift_client, name)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        out = u""
        out += u"|{0:^50}|{1:^25}|{2:^25}|\r\n".format(
            "Name",
            "# Objects",
            "Size"
        )
        for container in self.containers:
            out += u"|{0:^50}|{1:^25}|{2:^25}|\r\n".format(
                container['name'],
                container['count'],
                human_bytes(int(container['bytes']))
            )
        return out


class SwiftClientWrapper(object):
    def __init__(self, auth_package = None):
        if self._load_cached_credentials():
            logger.debug("Loaded credentials from cache")
        elif auth_package is not None:
            self.swift_token_manager = SwiftTokenManager(auth_package)
        else:
            raise Exception("No credential found")
        self._connect()

    def _load_cached_credentials(self):
        if os.path.exists(config.hubic_credential_cache):
            import pickle
            with open(config.hubic_credential_cache, 'rb') as f:
                self.swift_token_manager = pickle.load(f)
                return True
        return False

    def _update_credential_cache(self):
        import pickle
        with open(config.hubic_credential_cache, 'wb') as f:
            pickle.dump(self.swift_token_manager, f)

    def _connect(self):
        self.swift_client = swiftclient.client.Connection(
            preauthurl=self.swift_token_manager.endpoint,
            #preauthtoken="ff128c77ea2043939df97f61e030f68f",
            preauthtoken=self.swift_token_manager.token,
            retries=10,
            retry_on_ratelimit = True,
        )
        self._update_credential_cache()


    def put_object(self,*args, **kwargs):
        return self.swift_client.put_object(*args, **kwargs)

    def __getattr__(self, item):
        """
        Handles swift token renew when swift token has expired
        """
        def wrapper(method_name):
            def call(*args, **kwargs):
                for i in range(2):
                    try:
                        method = getattr(self.swift_client, method_name)
                        ret = method(*args, **kwargs)
                        return ret
                    except swiftclient.exceptions.ClientException as e: # Detect token expiration
                        if e.http_reason == 'Unauthorized':
                            logger.debug("Expired swift token, reconnecting")
                            self._connect()
                        else:
                            raise e

            return call
        return wrapper(item)