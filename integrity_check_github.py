import socket
import os
import re
import logging
import json
import hashlib 
import logging.handlers
import sys

"""
Script to check integrity between a main store (Master) and its backup (Slave) :
    * Will create a Db containing the hash of every files (this db need to be synced from the master to the slave)
"""


DIRECTORIES_ROOT=[{
			'prefix': u'/volume2',
			'path' : u'photo', 
			'excluded_ext' : [
				".json", 
				"THUMB_L.jpg", 
				"THUMB_M.jpg", 
				"THUMB_S.jpg",
				"THUMB_B.jpg",
				"THUMB_XL.jpg",
				]
		},]

DB_FILE="/volume2/hash_db/integrity_db.json"
MASTER = False # Set to True on the master Node
SMTP_SERVER = "ASPMX.L.GOOGLE.COM"
FROM_ADDR = "integrity_check@XXXX.fr"
TO_ADDR = "someone@gmail.com"


class BufferingSMTPHandler(logging.handlers.SMTPHandler):
    """
    BufferingSMTPHandler works like SMTPHandler log handler except that it
    buffers log messages until buffer size reaches or exceeds the specified
    capacity at which point it will then send everything that was buffered up
    until that point in one email message.  Contrast this with SMTPHandler
    which sends one email per log message received.
    """

    def __init__(self, mailhost, fromaddr, toaddrs, subject, credentials=None,
                 secure=None, capacity=1024, retry=5):
        logging.handlers.SMTPHandler.__init__(self, mailhost, fromaddr,
            toaddrs, subject,
            credentials, secure)
        self.retry = retry
        self.capacity = capacity
        self.buffer = []

    def emit(self, record):
        try:
            self.buffer.append(record)

            if len(self.buffer) >= self.capacity:
                self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def flush(self):
        # buffer on termination may be empty if capacity is an exact multiple of
        # lines that were logged--thus we need to check for empty buffer
        if not self.buffer:
            return
        for i in range(self.retry):
            try:
                import smtplib
                from email.utils import formatdate
                port = self.mailport
                if not port:
                    port = smtplib.SMTP_PORT
                smtp = smtplib.SMTP(self.mailhost, port)
                msg = ""
                for record in self.buffer:
                    msg = msg + self.format(record) + "\r\n"
                msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                    self.fromaddr,
                    ",".join(self.toaddrs),
                    self.getSubject(self.buffer[0]),
                    formatdate(), msg)
                if self.username:
                    if self.secure is not None:
                        smtp.ehlo()
                        smtp.starttls(*self.secure)
                        smtp.ehlo()
                    smtp.login(self.username, self.password)
                smtp.sendmail(self.fromaddr, self.toaddrs, msg)
                smtp.quit()
                self.buffer = []
                break
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                if i == (self.retry-1):
                    self.handleError(self.buffer[0])
                else:
                    time.sleep(10 + i*60)


def checkEncoding():
    sys_enc = sys.getfilesystemencoding()
    term_enc = sys.stdout.encoding
    if ( sys_enc != "UTF-8") or (sys.stdout.encoding != "UTF-8"):
        logger.warning("System encoding is not UTF8, there may be issues, please check !! \r\n\tFS encoding : %s\tconsole encoding : %s"%(sys_enc, term_enc))

def setUpLogging():
    ##
    #
    # Setting logging
    #
    ##
    global logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # File logger
    fh = logging.FileHandler('integrity_check.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    # Console logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    # SMTP logger
    sh = BufferingSMTPHandler(
        mailhost = SMTP_SERVER, 
        fromaddr = FROM_ADDR, 
        toaddrs = TO_ADDR, 
        subject = "Integrity check on %s" % socket.gethostname(),
        )
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.addHandler(sh)
    return logger

class Db (object):
    def __init__(self, path):
        self.path = path
        self.known_files = {} # 'path' : hash
        try:
            logger.info("Loading %s"%path)
            with open(path, 'rb') as f:
                self.known_files = json.load(f)
        except Exception as e:
            self.version = 0
            logger.warning("%s does not exists or corrupted, starting with an empty DB : %s"%(self.path,e))
            if not MASTER:
                raise Exception("Slave does not have a db")
    def save(self):
        os.rename(self.path, "%s_%s.bak"%(self.path,int(time.time()) ))
        try:
            with open(self.path, 'wb') as f:
                json.dump(self.known_files, f)
        except Exception as e:
            logger.error("could not save DB to %s : %s"%(self.path, e))
    @property
    def version(self):
        return self.known_files['@@@@DB_VERSION@@@@']    

    @version.setter
    def version(self, value):
        self.known_files['@@@@DB_VERSION@@@@'] = value
        logger.debug("db version is now %s"%value)
        
    def __len__(self):
        return len(self.known_files) - 1

    def __contains__(self,key):
        return key in self.known_files

    def __getitem__(self,key):
        return self.known_files[key]
        
    def __setitem__(self,key, value):
        if key in self:
            logger.error("File %s is already in DB!"%(key))
            return
        self.known_files[key] = value
        self.version += 1

def sha1(filepath):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as f:
        buf = f.read(1048576)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(1048576)
    return hasher.hexdigest()
    
    
def generateTree(root):
    # files_dict = {}
    # dirs_dict = {}
    for path, dirs, files in os.walk(root):
        for file in files:
            # files_dict[os.path.join(path, file)]=0
            yield os.path.join(path, file)
        # for dir in dirs:
            # dirs_dict[os.path.join(path,dir)]=0
    # return (dirs_dict,files_dict)

def check_integrity():
    global MASTER
    global DB_FILE
    global DIRECTORIES_ROOT
    errors=0
    files_ok = 0
    new_files = 0

    db = Db(DB_FILE)
    if len(db) == 0:
        logger.warning("DB is empty")

    for dir in DIRECTORIES_ROOT:
        print "Starting with %s"%dir
        full_path = os.path.join(unicode(dir['prefix']), unicode(dir['path']))
        files = generateTree(full_path)
        for f in files:
            f_without_prefix = re.sub("^%s/"%dir['prefix'], "", f)
            _continue = False
            if ('excluded_ext' in dir) and (len(dir['excluded_ext'])>0):
                for excluded_ext in dir['excluded_ext']:
                    if f.endswith(excluded_ext):
                        logger.debug("Ignoring %s"%(f))
                        _continue = True
                        continue
            if _continue:
                continue
            if f_without_prefix not in db:
                if MASTER is False:
                    logger.error("Unknown file found on slave (%s), db may be out of sync version = %s"%(f_without_prefix,db.version))
                    errors += 1
                    continue
                logger.debug("new file %s"%f)
                f_hash = sha1(f)
                db[f_without_prefix] = f_hash            
                new_files += 1
            else:
                f_hash = sha1(f)
                if f_hash != db[f_without_prefix]:
                    logger.critical("FATAL hash for %s does not match got %s, expected %s"%(f,f_hash,db[f_without_prefix]))
                    errors+=1
                else:
                    files_ok+=1
    if MASTER:
        db.save()
    logger.warning("Corrupted files : %s - New files : %s - Valid files : %s - Db version : %s"%(errors, new_files,files_ok, db.version ))    	    

    if not MASTER:
        if files_ok != len(db):
            logging.critical("Files are missing on slave : %s != %s"%(files_ok, len(db)))

setUpLogging()
try:
    checkEncoding()
#    check_integrity()
    logger.warning("test")
except Exception as e:
    logger.critical("CRASH while checking integrity : %s "%(e))
logging.shutdown()
