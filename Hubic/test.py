from utils import normpath, setUpLogging, human_bytes
logger = setUpLogging()
import config
from Hubic.hubic import Hubic


hubic=Hubic(config.auth_package)
hubic_files = hubic.getAllObjectsMetadataIndexedByPath( prefix = "Backup/NAS", ignored_exts=None, limit=None)
#hubic_files = hubic.getAllObjectsMetadataIndexedByPath(path="Backup/NAS/photo", prefix = "Backup/NAS", ignored_exts=None, limit=None)

print hubic
pass
exit()