import config
from Hubic.hubic import Hubic
import os
import logging
from utils import normpath, setUpLogging, human_bytes
from localstorage import LocalStorage

logger = setUpLogging()


#TODO
#   Ignore extentions


class DirectoriesComparator(object):
    def __init__(self):
        auth_package = config.auth_package
        self.hubic = Hubic(auth_package)
        self.localhost = LocalStorage()
        self.to_upload = []

    def do(self):
        for directory in config.DIRECTORIES_ROOT:
            local_prefix = normpath(directory['local_prefix'])
            hubic_prefix = normpath(directory['remote_prefix'])
            ignored_ext = directory['excluded_ext']
            local_path = normpath(os.path.join(local_prefix, directory['path']))
            hubic_path = normpath(os.path.join(hubic_prefix, directory['path']))
            logger.info("Checking [%s]%s <-> [%s]%s"%(local_prefix, directory['path'], hubic_prefix, directory['path']))
            hubic_files = self.hubic.getAllObjectsMetadataIndexedByPath(path=hubic_path, prefix = hubic_prefix, ignored_exts=ignored_ext, limit=None)
            local_files = self.localhost.getAllObjectsMetadataIndexedByPath(path=local_path, ignored_exts=ignored_ext, prefix=local_prefix)

            hubic_keyset = hubic_files.viewkeys()
            local_keyset = local_files.viewkeys()

            missing_on_hubic = local_keyset - hubic_keyset
            missing_on_local = hubic_keyset - local_keyset
            present_on_both = hubic_keyset & local_keyset

            self.handleMissingOnHubic(missing_on_hubic=missing_on_hubic, hubic_files=hubic_files, local_files=local_files, hubic_prefix=hubic_prefix)
            self.handleMissingOnLocal(missing_on_local=missing_on_local, hubic_files=hubic_files, local_files=local_files)
            self.handlePresentOnBoth(present_on_both=present_on_both, hubic_files=hubic_files, local_files=local_files)
        if config.upload_missing_files:
            self._createPrefixDirs(hubic_path)
            self.hubic.upload(self.to_upload)

    def _createPrefixDirs(self,hubic_prefix):
        dir_split = hubic_prefix
        while True:
            logging.debug("Creating prefix directory %s"%dir_split)
            self.hubic.createDirectory(dir_split)
            len_b = len(dir_split)
            dir_split = os.path.split(dir_split)[0]
            if len(dir_split) == len_b:
                break

    def handleMissingOnHubic(self, missing_on_hubic, hubic_files, local_files, hubic_prefix):
        logger.warning("%s files missing on hubic : %s"%(len(missing_on_hubic), missing_on_hubic))
        missing_size = sum([local_files[k]['bytes'] for k in missing_on_hubic])
        logger.warning("Missing file : %s"%(human_bytes(missing_size)))
        missing_files = [{'name': normpath(hubic_prefix + k),
                          'local_path': local_files[k]['name'],
                          'hash': local_files[k]['hash'],
                          'bytes': local_files[k]['bytes'],
                          'is_dir': local_files[k]['is_dir'],
                         } for k in missing_on_hubic
        ]
        self.to_upload += missing_files

    def handleMissingOnLocal(self, missing_on_local, hubic_files, local_files):
        logger.error("%s files missing on local : %s"%(len(missing_on_local), missing_on_local))


    def handlePresentOnBoth(self,present_on_both, hubic_files, local_files):
        valid_on_both = []
        invalid = []
        logger.info("%s files present on both sides"%(len(present_on_both)))
        for key in present_on_both:
            hubic_file = hubic_files[key]
            local_file = local_files[key]
            if local_file['is_dir']:
                continue #Don't compare hash for directories!
            hubic_md5 = hubic_file['hash']
            local_md5 = local_file['hash']
            if hubic_md5 == local_md5:
                logger.debug("MD5 matches for %s"%hubic_file)
                valid_on_both.append(key)
            else:
                logger.error("MD5 mismatch for file %s != %s"%(local_file, hubic_file))
                invalid.append(key)
        size_valid = sum([hubic_files[k]['bytes'] for k in valid_on_both])
        size_invalid = sum([hubic_files[k]['bytes'] for k in invalid])
        logger.warning("%s files valid (%s), %s files invalid (%s)"%(
            len(valid_on_both),
            human_bytes(size_valid),
            len(invalid),
            human_bytes(size_invalid)
            )
        )




a=DirectoriesComparator()
a.do()
logging.shutdown()
pass
