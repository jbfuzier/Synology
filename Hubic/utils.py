import hashlib
import logging
import logging.handlers
import os
import sys
import config
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socket
logger = logging.getLogger("%s.%s"%(config.appname, __name__))


def checkEncoding():
    sys_enc = sys.getfilesystemencoding()
    term_enc = sys.stdout.encoding
    if ( sys_enc != "UTF-8") or (sys.stdout.encoding != "UTF-8"):
        logger.warning("System encoding is not UTF8, there may be issues, please check !! (export LANG=en_US.utf8) \r\n\tFS encoding : %s\tconsole encoding : %s"%(sys_enc, term_enc))


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
                msg = MIMEMultipart("alternative")
                msg.set_charset("utf-8")
                msg["Subject"] = self.getSubject(self.buffer[0])
                msg["From"] = self.fromaddr
                msg["To"] = ",".join(self.toaddrs)
                msg_content = u""
                for record in self.buffer:
                    msg_content = msg_content + self.format(record) + "\r\n"
                msg_content = msg_content.encode('utf-8')
                part1 = MIMEText(msg_content, 'plain', 'utf-8')
                msg.attach(part1)
                if self.username:
                    if self.secure is not None:
                        smtp.ehlo()
                        smtp.starttls(*self.secure)
                        smtp.ehlo()
                    smtp.login(self.username, self.password)
                smtp.sendmail(self.fromaddr, self.toaddrs, msg.as_string())
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



def totalSize(file_dict):
    return sum([f['bytes'] for f in file_dict.values()])


def setUpLogging():
    ##
    #
    # Setting logging
    #
    logger = logging.getLogger(config.appname)
    logger.setLevel(config.console_logging_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # File logger
    if config.file_logging:
        fh = logging.FileHandler(config.log_file)
        fh.setLevel(config.file_logging_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    # Console logger
    ch = logging.StreamHandler()
    ch.setLevel(config.console_logging_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if config.smtp_logging:
        # SMTP logger
        sh = BufferingSMTPHandler(
            mailhost = config.smtp_host,
            fromaddr = config.smtp_sender,
            toaddrs = config.smtp_receiver,
            subject = "Hubic Sync on %s" % socket.gethostname(),
        )
        sh.setLevel(config.smtp_logging_level)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger



def human_bytes(num):
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

def normpath(path):
    """
    Normalize path between linux & windows to compare them
    """
    return os.path.normpath(path).replace("\\", "/")

def generateTree(root):
    yield root
    for path, dirs, files in os.walk(root):
        for file in files:
            yield os.path.join(path, file)
        for dir in dirs:
            yield os.path.join(path, dir)


def sha1(filepath):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as f:
        buf = f.read(1048576)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(1048576)
    return hasher.hexdigest()

def md5(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(1048576)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(1048576)
    return hasher.hexdigest()


def checkEncoding():
    sys_enc = sys.getfilesystemencoding()
    term_enc = sys.stdout.encoding
    if ( sys_enc != "UTF-8") or (sys.stdout.encoding != "UTF-8"):
        logger.warning("System encoding is not UTF8, there may be issues, please check !! \r\n\tFS encoding : %s\tconsole encoding : %s"%(sys_enc, term_enc))
