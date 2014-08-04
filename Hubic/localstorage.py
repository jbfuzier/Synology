import os
import logging
from utils import md5, generateTree, normpath
from datetime import datetime
import config

logger = logging.getLogger("%s.%s"%(config.appname, __name__))

class LocalStorage(object):
    def __init__(self):
        pass

    def getAllObjectsMetadataIndexedByPath(self, path, ignored_exts=None, prefix=None):
        """
            {
                u'/volume/toto' : {u'name': '/volume/toto', 'hash' : 'md5hash', 'last_modified': '', 'bytes': '193'}
            }
        """
        files_dict = {}
        files = generateTree(path)
        for file in files:
            file = normpath(file)
            if ignored_exts is not None:
                for ign_ext in ignored_exts:
                    if file.endswith(ign_ext):
                        logger.debug("Ignoring file %s (based on extension)"%(file))
                        continue
            file_metadata = {
                'name': file,
                'hash': md5(file),
                'last_modified': datetime.fromtimestamp(os.path.getmtime(file)),
                'bytes': os.path.getsize(file),
                }
            if prefix is not None:
                file_k = file.replace(prefix, "")
            files_dict[file_k] = file_metadata
        return files_dict
