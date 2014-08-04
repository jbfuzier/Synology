hubic_credential_cache = "hubic_credential_cache.pickle"
retry = 10
backoff = 10 #Time between attempts
timeout = 10 #timeout for http requests
upload_missing_files = True

"""
    Logging Config
"""
import logging
import socket
console_logging_level = logging.DEBUG
smtp_logging = True
smtp_logging_level = logging.INFO
smtp_host = "smtp.XXXX.fr"
smtp_sender = "%s@XXXX.fr"%(socket.gethostname())
smtp_receiver = "someone@XXXX.com"
file_logging = True
file_logging_level = logging.DEBUG
log_file = "hubic_sync.log"
appname = "hubicsync"



DIRECTORIES_ROOT=[{
                  'local_prefix': u'C:\\Users\\jb\\Desktop\\',
                  'remote_prefix': u'Backup',
                  'path' : u'hubictest',
                  'excluded_ext' : [
                      ".json",
                      "THUMB_L.jpg",
                      "THUMB_M.jpg",
                      "THUMB_S.jpg",
                      "THUMB_B.jpg",
                      "THUMB_XL.jpg",
                      ]
                  },]


from Hubic.hubic import AuthPackage
auth_package = AuthPackage(
    username="hubicuser@mail.com", # Used to authenticate to the Oauth Page
    password="hubicpassword",
    hubic_client_id="", # ID of the app (generated in the hubic web app)
    hubic_client_secret="", #PWD of the app
)