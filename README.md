Synology
========

Scripts related to synology backup (rsync &amp; hubic) &amp; data corruption detection 


### Script to backup a Synology NAS to hubic : 
https://github.com/jbfuzier/Synology/tree/master/Hubic


### Script to check data integrity between a master node and it's backup
* Compute hash of every file, keep it in a "db" (simple json file)
* Sync the json file between the nodes
* Both node will check file integrity based on this json file (in my use case = archiving, files should not change; if they do it is a sign of silent corruption)
* Master will add new files to the db, slave will not (and will report new files as an error)

####integrity_check_github.py
All in one (messy) file, config inside the file

#### raid_scrub.sh
Simple shell script to perform periodical raid scrub (to detect raid incoherences), change RAID_ARRAY and MAIL_TO according to your needs.
Require : nail to send email (installable via ipkg on synology)

### Want to get more paranoid about data integrity :
http://www.zdnet.com/has-raid5-stopped-working-7000019939/
http://arstechnica.com/information-technology/2014/01/bitrot-and-atomic-cows-inside-next-gen-filesystems/
http://www.zdnet.com/blog/storage/data-corruption-is-worse-than-you-know/191


### To run scripts from synology task scheduler
* Install python2.X package
* Add those two lines before calling any .py script (ensure filenames get read properly) :
    export LANG="en_US.utf8"
    export LC_ALL="en_US.utf8"
    Example :
        export LANG="en_US.utf8"
        export LC_ALL="en_US.utf8"
        python /volume2/homes/XXX/Hubic/main.py


### What is my backup strategy ?
* 2 Nas in raid6 synced via Rsync
* Raid scrub every month
* Data integrity check (against a sha1) on each side every month
* + TODO : copy on hubic
