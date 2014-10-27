# Synology backup to HUBIC


## Use case
Backup the (part) of the content of a synology NAS to hubic.com (OVH)

My use case is to back up static content (mostly pictures & videos) :
* If a file is present on the NAS but not on hubic, it should be uploaded
* If a file is present both on hubic and on the NAS, we check the MD5 on both sides, if the MD5 does not match, the file could be either corrupted on the NAS or updated (which should not happen in my use case -> log error)
* If a file is present on hubic but not on the NAS -> log an error


## What's behind hubic ?
Hubic is based on openstack swift which allows to store a large amount of files and maintains file integrity & availability by replicating the file to 3 servers.
A md5 digest is stored as metadata in order to detect file corruption.
File are regularly read and check against their checksums by openstack to avoid silent corruption (I do not know how often hubic does those checks)(See bit rot : http://en.wikipedia.org/wiki/Data_rot)

## A word about Raid & NAS
* Raid is NOT a backup solution, it is just a way to ensure data availability
* Raid DOES NOT guarantee data integrity in any way !
* Raid can even be in an inconsistent state (where the two mirrored blocks does not match) without any alarm raised (see RAID scrubbing for a solution)
* Ext3, 4 DOES NOT guarantee data integrity (only filesystems such as ZFS allows that but that comes with higher complexity and overhead)
* Raid, Ext (or whatever filesystem) WILL NOT detect data corruption

## Proper strategy
* When you store a new file, keep a hash of this file
* When you do your backup, does not blindly copy your main store to your backup store (you might be copying corrupted data) : file hash must be checked first
* If you use Rsync as a backup solution (I do), the default option (without --checksum) will only looks at metadata to decide whether or not the file has changed (in this use case, this is perfect as this avoid copying corrupted files to the backup)
* Periodically check main store & backup store files integrity 

## How does hubic/openstack handles those issues ?
* By computing periodically a hash of every files and checking it against the hash value stored when the file was sent by the user

## Dependencies
python-swiftclient is needed, you can install it through pip :

> wget https://bootstrap.pypa.io/get-pip.py
> python get-pip.py

Once pip is installed :
>pip install python-swiftclient

## How to use this script ?
* Copy config_sample.py to config.py and edit it according to your needs
* You will need to register an app on hubic on your account in order to access the API from your NAS (more details here : https://api.hubic.com/sandbox/). Once you have created your app you will get an app id and secret that need to be set up in the config file.


### To run scripts from synology task scheduler
* Install python2.X package
* Add those two lines before calling any .py script (ensure filenames get read properly) :
    export LANG="en_US.utf8"
    export LC_ALL="en_US.utf8"
    Example :
        export LANG="en_US.utf8"
        export LC_ALL="en_US.utf8"
        python /volume2/homes/XXX/Hubic/main.py
