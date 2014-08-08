from utils import normpath, setUpLogging, human_bytes
logger = setUpLogging()
import config
from Hubic.hubic import Hubic
import logging

hubic=Hubic(config.auth_package)
hubic_files = hubic.getAllObjectsMetadataIndexedByPath( prefix = "Backup/NAS", ignored_exts=None, limit=None)
#hubic_files = hubic.getAllObjectsMetadataIndexedByPath(path="Backup/NAS/photo", prefix = "Backup/NAS", ignored_exts=None, limit=None)

logger.error(u'\u3053\u3093\u306b\u3061\u306f\u3001\u4e16\u754c\uff01\n')
logging.shutdown()
print hubic
pass
exit()