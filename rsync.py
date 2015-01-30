import datetime
import os
import subprocess


def send_mail(subject, rcpt, data):
    mail_cmd = "echo '{2}'|mail -s '{0}' {1}".format(
        subject,
        rcpt,
        data
        )
    os.system(mail_cmd)

##
#
#   CONFIG VARS
#
##
rsync_folders = [
    {
        'src': "root@192.168.92.254:/volume1/music/",
        'dst': "/mnt/tank/nas92_backup/music",
    },
    {
        'src': "root@192.168.92.254:/volume1/photo/",
        'dst': "/mnt/tank/nas92_backup/photo",
    },
    {
        'src': "root@192.168.92.254:/volume1/video/",
        'dst': "/mnt/tank/nas92_backup/video",
    },
    {
        'src': "root@192.168.92.254:/volume1/Misc/",
        'dst': "/mnt/tank/nas92_backup/Misc",
    },
    {
        'src': "root@192.168.92.254:/volume1/Progz/",
        'dst': "/mnt/tank/nas92_backup/Progz",
    },
]
rcpt = "XXXXXX@gmail.com"
logfile_path = "/var/log/rsync.log"
rsync_path = "/usr/local/bin/rsync"
recycle_dir_path = "/mnt/tank/nas92_backup/@Rsync_Recycle"
##
#
# END OF CONFIG
#
##


# Keep a copy of deleted or updated file in recycle
recycle_dir = os.path.join(recycle_dir_path, datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M"))
has_error = False
full_output = ""
for rsync_folder_pair in rsync_folders:
    msg = "Syncing %s -> %s\r\n"%(rsync_folder_pair['src'], rsync_folder_pair['dst'])
    full_output += "\r\n"*10
    full_output += msg
    print msg
    rsync_cmd = "{0} -r -t -z --delete-delay -v --backup --backup-dir {4} --bwlimit=100 --log-file={1} --progress -h -e 'ssh -p 22 -o BatchMode=yes -o StrictHostKeyChecking=yes' {2} {3}".format(
        rsync_path,
        logfile_path,
        rsync_folder_pair['src'],
        rsync_folder_pair['dst'],
        recycle_dir
    )
    print rsync_cmd
    try:
        output = subprocess.check_output(rsync_cmd, shell=True)
    except CalledProcessError as e:
        # If return code !=0
        has_error = True
        print "{0} returned code {1}".format(e.cmd, e.returncode)
        output = e.output
        send_mail(
        "Rsync failed for %s -> %s"%(rsync_folder_pair['src'], rsync_folder_pair['dst']),
        rcpt,
        output
        )
    print output
    full_output += output

recycle_du = subprocess.check_output("du -h -d 1 {0}".format(recycle_dir_path), shell=True)
print recycle_du
full_output+= "\r\n"*10
full_output+=recycle_du
if not has_error:
    send_mail("OK : No Error while backing up", rcpt, full_output)
    exit(0)
else:
    send_mail("KO : Error while backing up", rcpt, "There were errors while backing up, please check previous mail for details")
    exit(2)


