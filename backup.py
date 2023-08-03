#!/usr/bin/env python3

from xml.etree import ElementTree
import argparse
import os
import sys
import xmlutil
import osutil
import datetime
import re
import logging
import traceback
from textwrap import dedent

"""
Backup solution
- Uses pre-defined profiles to backup data
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
2023-07-26   refactoring + automated tests

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

def _remove_incremental_backup(folder, args):
    """Removes an incremental backup."""
    if not os.path.exists(folder):
        if args.verbose:
            print(f'Folder does not exist: {folder}')
        return
    osutil.execute_command(["rm", "-rf", folder], shell=False, verbose=args.verbose, simulate=args.simulate)

# def _move_incremental_backup(source, target, args):
    # """Moves an incremental backup."""
    # if not os.path.exists(source):
        # if args.verbose:
            # print(f'Source does not exist: {source}')
        # return
    # osutil.execute_command(["mv", source, target], shell=False, verbose=args.verbose, simulate=args.simulate)
    
def _copy_incremental_backup(source, target, args):
    """Copies an incremental backup."""
    if not os.path.exists(source):
        if args.verbose:
            print(f'Source does not exist: {source}')
        return
    if os.path.abspath(source) == os.path.abspath(target):
        if args.verbose:
            print(f'Source and target are equal: {source}')
        return
    osutil.execute_command(["cp", "-al", source, target], shell=False, verbose=args.verbose, simulate=args.simulate)

def _analyse_backup_folder(dir, backupCount):
    """Analyse backup folder and returns the folder to copy and all folders to delete."""
    now = datetime.datetime.now()
    folderName = now.strftime("%Y-%m-%d")
    toUse = os.path.join(dir, folderName)
    toCopy = None
    toDelete = None

    # get folders
    dirs = set()
    for f in os.listdir(dir):
        path = os.path.join(dir, f)
        if os.path.isdir(path):
            dirs.add(os.path.abspath(path))
    
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
    
    logging.debug(f'Folder to use:    {toUse}')
    logging.debug(f'Folder to copy:   {toCopy}')
    logging.debug(f'Folder to delete: {toDelete}')
    return toUse, toCopy, toDelete

def _check_pre_conditions(source, target):
    """Check pre-conditions."""
    if not os.path.exists(source):
        raise Exception(f'Source does not exist: {source}')
    if len(os.listdir(source)) == 0:
        raise Exception(f'Source is empty: {source}')
    if not os.path.exists(target):
        raise Exception(f'Target does not exist: {target}')

def _sync_dirs(profile, source, target, args, prompt=False):
    """Synchronize source to target."""
    # normalize file paths
    if not source.endswith("/"):
        # force the trailing slash to copy the content of the source directory
        source += "/"
    if not target.endswith("/"):
        target += "/"
    
    print(f'Synchronizing from {source} to {target}')
    if prompt and not args.simulate and not getYesOrNo('Do you want to continue?', None):
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
    osutil.execute_command(cmd, verbose=args.verbose)

def backup(profile, args):
    """Creates backups of the given profile.
    See: http://www.linuxwiki.de/rsync/SnapshotBackups
    See: http://www.mikerubel.org/computers/rsync_snapshots/
    """
    source = profile.source
    target = profile.target
    _check_pre_conditions(source, target)
            
    # print message
    print(f'===== Backup profile: {profile.name}')
    info = f'Starting backup from {source} to {target}'
    if args.simulate:
        info += ' (dry-run)'
    print(info)
    print()
    
    if profile.mode == MODE_INCR:
        # analyse backup folder
        toUse, toCopy, toDelete = _analyse_backup_folder(target, backupCount=profile.backupCount)

        # Remove oldest backup: rm -rf backup.max
        if toDelete is not None:
            print(f'Removing oldest backup: {toDelete}')
            _remove_incremental_backup(toDelete, args)

        # copy last backup into new one: cp -al backup.0 backup.1
        if toCopy is not None:
            print(f'Copying newest incremental backup: {toCopy}')
            _copy_incremental_backup(toCopy, toUse, args)
        
        # set target to first incremental backup 
        target = toUse
        if args.simulate and toCopy is not None:
            target = toCopy

    # synchronize source to target
    _sync_dirs(profile, source, target, args)

def restore(profile, args):
    """Restore backup of the given profile (switch source/target).
    """
    # switch target and source
    target = profile.source
    source = profile.target
    _check_pre_conditions(source, target)

    # print message
    print(f'===== Restore profile: {profile.name}')
    info = f'Restore backup from {source} to {target}'
    if args.simulate:
        info += ' (dry-run)'
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
            raise Exception(f'No incremental backup found: {source}')

    # synchronize source to target
    _sync_dirs(profile, source, target, args, prompt=True)
    
def parse_xml_file(file):
    """Parses the xml file."""
    tree = ElementTree.parse(file)
    root = tree.getroot()
    errors = []
    profiles = []
    usedNames = set()
    for child in root:
        profile = BackupProfile()
        profile.name = xmlutil.parse_xml_tag(child, "name")
        profile.description = xmlutil.parse_xml_tag(child, "description")
        profile.source = xmlutil.parse_xml_tag(child, "source")
        profile.target = xmlutil.parse_xml_tag(child, "target")
        profile.options = xmlutil.parse_xml_tag_list(child, "option")
        mode = xmlutil.parse_xml_tag(child, "mode")
        if mode is not None:
            profile.mode = mode
        backupCount = xmlutil.parse_xml_tag(child, "count")
        if backupCount is not None:
            profile.backupCount = int(backupCount)
        profiles.append(profile)
            
        # validate profile
        if profile.name is None:
            errors.append(f'{profile.name}: Tag <name> is required.')
        if profile.name in usedNames:
            errors.append(f'{profile.name}: A profile with this name already exists.')
        usedNames.add(profile.name)
        if profile.source is None:
            errors.append(f'{profile.name}: Tag <source> is required.')
        if profile.target is None:
            errors.append(f'{profile.name}: Tag <target> is required.')
        if profile.mode not in (MODE_INCR, MODE_SYNC):
            errors.append(f'{profile.name}: Unsupported mode: "{profile.mode}" -> allowed values are "{MODE_INCR}" or "{MODE_SYNC}".')
    return profiles, errors

def print_profile_detail(profile):
    print(f'===== {"Profile":<11}: {profile.name}')
    print(f'  {"Description":<15}: {profile.description}')
    print(f'  {"Source":<15}: {profile.source}')
    print(f'  {"Target":<15}: {profile.target}')
    print(f'  {"Mode":<15}: {profile.mode}')
    print(f'  {"Options":<15}: {profile.options}')
    if profile.mode == MODE_INCR:
        print(f'  {"Backup Count":<15}: {profile.backupCount}')

def print_available_profiles(profiles):
    print('Available backup profiles: ')
    for p in profiles:
        print(f'  {p.name:<15}: {p.description}')

def _findProfileDefinitionFile(fileName):
    """Searches for a file using following order:
	1. in current working dir: ./<fileName>
    2. in $home directory: ~/.tools/<fileName>
    3. in script folder: <scriptDir>/<fileName>
    """
    fileCandidates = []
    if os.path.isabs(fileName):
        fileCandidates.append(fileName)
    else:
        fileCandidates.append(os.path.join(os.getcwd(), fileName))
        fileCandidates.append(os.path.join(os.path.expanduser("~user"), ".tools", fileName))
        fileCandidates.append(os.path.join(os.path.dirname(os.path.realpath(os.path.abspath(__file__))), fileName))
    
    for f in fileCandidates:
        if os.path.exists(f): 
            return f, fileCandidates
    return None, fileCandidates

def getYesOrNo(question, default=True):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    prompt = {True: " [Y/n] ", False: " [y/N] ", None: " [y/n] "}
    while True:
        print(question + prompt[default], end='')
        choice = input().lower()
        if default is not None and choice == "":
            return default
        elif choice in valid:
            return valid[choice]
        else:
            print('Please respond with "yes" or "no" (or "y" or "n").')

def main(argv=None):
    try:
        # parse arguments
        parser = argparse.ArgumentParser(description='Backup solution with pre-defined profiles including support for incremental backups with storage space optimization.', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--debug', help='activate DEBUG logging', action='store_true')
        parser.add_argument('--file', help='profile definition file (default: backup.xml)', default='backup.xml')
        parser.add_argument('-v', '--verbose', action='store_true', help='print verbose output')
        parser.add_argument('-n', '--dry-run', action='store_true', dest='simulate', help='simulate backup process')
        parser.add_argument('-p', '--profile-details', action='store_true', dest='profileDetails', help='show all details of specified profiles')
        parser.add_argument('-t', '--print-profile-template', dest='printTemplate', action='store_true', help='print XML profile template file to stdout')
        parser.add_argument('--delete', action='store_true', help='delete files on target if they no longer exist')
        parser.add_argument('--restore', action='store_true', help='restore backup to source directory (switch source/target)')
        parser.add_argument('--restore-date', dest='restoreDate', help='date of backup to restore for incremental backups')
        parser.add_argument('profile', nargs='*', help='name of profile to backup')
        args = parser.parse_args(argv)

        # init logging
        level = logging.DEBUG if args.debug else logging.WARNING
        logging.basicConfig(format='%(levelname)s: %(message)s', level=level, force=True)
        
        if args.printTemplate:
            defaultTemplate = BackupProfile()
            xml = f"""\
                <?xml version="1.0" encoding="UTF-8"?>
                <backup-profiles>
                    <backup-profile>
                        <name>PROFILE NAME</name>
                        <description>PROFILE DESCRIPTION</description>
                        <source>SOURCE FOLDER</source>
                        <target>TARGET FOLDER</target>
                        <!-- Optional: {MODE_INCR} or {MODE_SYNC} -->
                        <mode>{defaultTemplate.mode}</mode>
                        <!-- Optional: add one or more rsync options -->
                        <option>-rltvzi</option>
                        <!-- Optional: max. number of incremental backups that must not be deleted -->
                        <count>{defaultTemplate.backupCount}</count>
                    </backup-profile>
                </backup-profiles>"""
            print(dedent(xml))
            exit(0)

        # read all defined backup profiles
        file, fileCandidates = _findProfileDefinitionFile(args.file)
        if file:
            logging.debug(f'Parsing definition file: {file}')
            definedProfiles, errors = parse_xml_file(file)
            if errors:
                print(f'Definition file: {file}')
                print()
                print(f'Error while parsing definition file:')
                for e in errors:
                    print(f'  {e}')
                exit(1)
        else:
            print('Definition file not found:')
            for f in fileCandidates:
                print(f'  {f}')
            exit(1)
        
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
                print(f'Profile "{name}" not found')
            print()
            print_available_profiles(definedProfiles)
            exit(1)

        # print profile details
        if args.profileDetails:
            print(f'Definition file: {file}')
            print()
            for i, profile in enumerate(foundProfiles):
                if i > 0:
                    print()
                print_profile_detail(profile)
            exit(0)

        # perform action
        for i, profile in enumerate(foundProfiles):
            if i > 0:
                print()
            if args.restore:
                restore(profile, args)
            else:
                backup(profile, args)
    except Exception as e:
        print(e)
        if args.debug:
            traceback.print_exc()

if __name__ == '__main__':
    main()
