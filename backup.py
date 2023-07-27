#!/usr/bin/env python3

from xml.etree import ElementTree
import argparse
import os
import utils
import datetime
import re

"""
Backup solution
- Uses pre-defined profiles to backup data (less writing, less error-prone)
- Supports synchronization and incremental backups

Incremental Backup's Folder Structure:
.../2013-11-20 -> newest/current backup
.../2013-11-15
.../2013-11-10
.../2013-11-05 -> oldest backup

History:
2013-05-30   initial version
2013-11-28   use date as folder name for incremental mode
2018-03-07   support multiple profiles

"""

MODE_SYNC = "synchronize"  # support only one backup by synchronizing two directories
MODE_INCR = "incremental"  # support several versions of old backups

class BackupProfile:
    """Backup profile definition."""
    def __init__(self):
        # default values
        self.name = "Undefined"
        self.description = None
        self.source = None
        self.target = None
        self.mode = MODE_SYNC
        self.options = None
        self.backupCount = 3

def _remove_incremental_backup(folder):
    """Removes an incremental backup."""
    if not os.path.exists(folder):
        if args.verbose:
            print("Folder does not exist: " + folder)
        return
    utils.execute_command(["rm", "-rf", folder], shell=False, verbose=args.verbose, simulate=args.simulate)

def _move_incremental_backup(source, target):
    """Moves an incremental backup."""
    if not os.path.exists(source):
        if args.verbose:
            print("Source does not exist: " + source)
        return
    utils.execute_command(["mv", source, target], shell=False, verbose=args.verbose, simulate=args.simulate)
    
def _copy_incremental_backup(source, target):
    """Copies an incremental backup."""
    if not os.path.exists(source):
        if args.verbose:
            print("Source does not exist: " + source)
        return
    utils.execute_command(["cp", "-al", source, target], shell=False, verbose=args.verbose, simulate=args.simulate)

def _analyse_backup_folder(dir, backupCount):
    """Analyse backup folder and returns the folder to copy and all folders to delete."""
    now = datetime.datetime.now()
    folderName = now.strftime("%Y-%m-%d")
    toUse = os.path.join(dir, folderName)

    toCopy = None
    toDelete = None
    dirs, files = utils.get_files([dir], recursive=False)
    # filter by date pattern
    dirs = [d for d in dirs if re.match("^\d\d\d\d-\d\d-\d\d$", os.path.basename(d)) is not None]
    dirs = sorted(dirs)
    dirs.reverse()
    if len(dirs) > 0:
        toCopy = dirs[0]
        if toCopy == toUse:
            # copy not necessary if source and target are the same dir
            toCopy = None
        elif len(dirs) >= backupCount:
            #toDelete = dirs[backupCount-1:len(dirs)]
            toDelete = dirs[-1]
    #print("use: " + str(toUse))
    #print("copy: " + str(toCopy))
    #print("delete: " + str(toDelete))
    return toUse, toCopy, toDelete

def _check_pre_conditions(source, target):
    """Check pre-conditions."""
    if not os.path.exists(source):
        raise Exception("Source does not exist: " + source)
    if len(os.listdir(source)) == 0:
        raise Exception("Source is empty: " + source)
    if not os.path.exists(target):
        raise Exception("Target does not exist: " + target)

def _sync_dirs(source, target, prompt=False):
    """Synchronize source to target."""
    # normalize file paths
    if not source.endswith("/"):
        # force the trailing slash to copy the content of the source directory
        source += "/"
    if not target.endswith("/"):
        target += "/"
    
    print("Synchronizing from " + source + " to " + target)
    if prompt and not utils.prompt_yes_no(simulate=args.simulate):
        return
    cmd = list()
    cmd.append("rsync")
    if len(profile.options) != 0:
        for option in profile.options:
            cmd.append(option)
    else:
        cmd.append("-avi")
    
    cmd.append("--progress")
    if args.delete:
        cmd.append("--delete")
    if args.simulate:
        cmd.append("-n")
        
    cmd.append(source)
    cmd.append(target)
    utils.execute_command(cmd, verbose=args.verbose)

def backup(profile):
    """Creates backups of the given profile.
    See: http://www.linuxwiki.de/rsync/SnapshotBackups
    See: http://www.mikerubel.org/computers/rsync_snapshots/
    """
    source = profile.source
    target = profile.target
    _check_pre_conditions(source, target)
            
    # print message
    print("===== Backup profile: " + profile.name)
    info = "Starting backup from " + source + " to " + target
    if args.simulate:
        info += " (dry-run)"
    print(info)
    print()
    
    if profile.mode == MODE_INCR:
        # analyse backup folder
        toUse, toCopy, toDelete = _analyse_backup_folder(target, backupCount=profile.backupCount)

        # Remove oldest backup: rm -rf backup.max
        if toDelete is not None:
            print("Removing oldest backup: " + toDelete)
            _remove_incremental_backup(toDelete)

        # copy last backup into new one: cp -al backup.0 backup.1
        if toCopy is not None:
            print("Copying newest incremental backup: " + toCopy)
            _copy_incremental_backup(toCopy, toUse)
        
        # set target to first incremental backup 
        target = toUse
        if args.simulate and toCopy is not None:
            target = toCopy

    # synchronize source to target
    _sync_dirs(source, target)

def restore(profile):
    """Restore backup of the given profile (switch source/target).
    """
    # switch target and source
    target = profile.source
    source = profile.target
    _check_pre_conditions(source, target)

    # print message
    print("===== Restore profile: " + profile.name)
    info = "Restore backup from " + source + " to " + target
    if args.simulate:
        info += " (dry-run)"
    print(info)
    print()

    if profile.mode == MODE_INCR:
        if args.restoreDate is not None:
            source = os.path.join(source, args.restoreDate)
        else:
            # use latest backup for restore

            # analyse backup folder
            toUse, toCopy, toDelete = _analyse_backup_folder(source, backupCount=profile.backupCount)

            # set source to latest incremental backup 
            if toCopy is None:
                source = toUse
            else:
                source = toCopy

        if not os.path.exists(source):
            raise Exception("No incremental backup found: " + source)

    # synchronize source to target
    _sync_dirs(source, target, prompt=True)
    
def parse_xml_file(file):
    """Parses the xml file."""
    tree = ElementTree.parse(file)
    root = tree.getroot()
    profiles = list()
    for child in root:
        profile = BackupProfile()
        profile.name = utils.parse_xml_tag(child, "name", required=True)
        profile.description = utils.parse_xml_tag(child, "description")
        profile.source = utils.parse_xml_tag(child, "source", required=True)
        profile.target = utils.parse_xml_tag(child, "target", required=True)
        profile.options = utils.parse_xml_tag_list(child, "option")
        mode = utils.parse_xml_tag(child, "mode")
        if mode is not None:
            profile.mode = mode
        backupCount = utils.parse_xml_tag(child, "count")
        if backupCount is not None:
            profile.backupCount = int(backupCount)
        profiles.append(profile)
    return profiles

def print_profile_help(profile):
    print("===== {0:<10}: {1}".format("Profile", profile.name))
    print(" {0:<15}: {1}".format("Description", profile.description))
    print(" {0:<15}: {1}".format("Source", profile.source))
    print(" {0:<15}: {1}".format("Target", profile.target))
    print(" {0:<15}: {1}".format("Mode", profile.mode))
    print(" {0:<15}: {1}".format("Options", profile.options))
    if profile.mode == MODE_INCR:
        print(" {0:<15}: {1}".format("Backup Count", profile.backupCount))

def print_available_profiles(profiles):
    print("Available backup profiles: ")
    for p in profiles:
        print(" {0:<15}: {1}".format(p.name, p.description))

if __name__ == "__main__":
    try:
        # parse arguments
        parser = argparse.ArgumentParser(description="Backup solution for pre-defined profiles.", formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("-v", "--verbose", action="store_true", help="print verbose output")
        parser.add_argument("-n", "--dry-run", action="store_true", dest="simulate", help="simulate backup process")
        parser.add_argument("-p", "--profilehelp", action="store_true", dest="profilehelp", help="show all details of specified profiles")
        parser.add_argument("--delete", action="store_true", help="delete files on target if they no longer exist")
        parser.add_argument("--restore", action="store_true", help="restore backup to source directory (switch source/target)")
        parser.add_argument("--restoredate", dest="restoreDate", help="date of backup to restore for incremental backups")
        parser.add_argument("profile", nargs="*", help="name of profile to backup")
        args = parser.parse_args()

        # read all defined backup profiles
        file = utils.findFile(fileName="backup.xml")
        if os.path.exists(file):
            #print("Reading definition: " + file)
            definedProfiles = parse_xml_file(file)
        else:
            exit("Definition file not found: " + file)
        
        # No profile given
        if not args.profile:
            print_available_profiles(definedProfiles)
            exit(0)

        # find given profiles
        nonFoundProfileNames = list()
        foundProfiles = list()
        for name in args.profile:
            profile = next((p for p in definedProfiles if p.name == name), None)
            if profile is None:
                nonFoundProfileNames.append(name)
            else:
                foundProfiles.append(profile)
                
        # check if all given profiles are available, else exit        
        if nonFoundProfileNames:
            for name in nonFoundProfileNames:
                print("Illegal profile: " + name)
            print()
            print_available_profiles(definedProfiles)
            exit(1)

        # print profile help
        if args.profilehelp:
            print("Definition file: " + file)
            print()
            for i, profile in enumerate(foundProfiles):
                if i > 0:
                    print()
                print_profile_help(profile)
            exit(0)

        # perform action
        for i, profile in enumerate(foundProfiles):
            if i > 0:
                print()
            if args.restore:
                restore(profile)
            else:
                backup(profile)
    except Exception as e:
        print(e)
#        raise e
        exit(1)

