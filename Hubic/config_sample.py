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
smtp_logging = True # Enable/disable email report
smtp_logging_level = logging.INFO
smtp_host = "smtp.XXXX.fr" # Smtp server to send mail from
smtp_sender = "%s@XXXX.fr"%(socket.gethostname()) # From field for email
smtp_receiver = "someone@XXXX.com" 
file_logging = True
file_logging_level = logging.DEBUG
log_file = "hubic_sync.log"
appname = "hubicsync"


# Select which directories to sync
DIRECTORIES_ROOT=[{ # In this example we want to sync C:\\Users\\jb\\Desktop\\hubictest 
                    # to Hubic under the location \Backup\hubictest
                  'local_prefix': u'C:\\Users\\jb\\Desktop\\', 
                  'remote_prefix': u'Backup',
                  'path' : u'hubictest', # Directory to sync
                  'excluded_ext' : [ # File extensions to ignore
                      ".json",
                      "THUMB_L.jpg",
                      "THUMB_M.jpg",
                      "THUMB_S.jpg",
                      "THUMB_B.jpg",
                      "THUMB_XL.jpg",
                      ]
                  },
                  {
                  'local_prefix': u'/volume1/',
                  'remote_prefix': u'Backup',
                  'path' : u'pictures',
                  'excluded_ext' : [
                      ".json",
                      "THUMB_L.jpg",
                      "THUMB_M.jpg",
                      "THUMB_S.jpg",
                      "THUMB_B.jpg",
                      "THUMB_XL.jpg",
                      ]
                  },
                    # ...
                  ]


from Hubic.hubic import AuthPackage
auth_package = AuthPackage(
    username="hubicuser@mail.com", # Used to authenticate to the Oauth Page
    password="hubicpassword",
    hubic_client_id="", # ID of the app (generated in the hubic web app)
    hubic_client_secret="", #PWD of the app
)
