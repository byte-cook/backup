# Backup.py

Backup.py is your solution to backup your data!

Backup.py provides the following features:
- Support for incremental backups: only back up data that has changed since the previous backup
- Optimize memory usage: Avoid to store the same file several times
- Define backup profiles once: Use these profiles for your regular backup tasks
- Easy to use: several profiles can be executed with a single command

## Install

Backup.py uses rsync:
```bash
apt install rsync
```

## Profile definiton

Define your backup profile in the definition file "backup.xml". By default this file is searched in the same folder as backup.py.

The XML structure is as follows:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<backup-profiles>
	<backup-profile>
		<name>home2nas</name>
		<description>Backup /home/user</description>
		<source>/home/user/</source>
		<target>/mnt/nas/user/desktop-home</target>
		<mode>synchronize</mode>
		<option>-rltvzi</option>
		<!-- .thumbnails: gnome thumbnails -->
		<option>--exclude=/.thumbnails/</option>
		<!-- .cache: cache data of applications -->
		<option>--exclude=/.cache/</option>
		<!-- Skip symlinks -->
		<option>--no-links</option> 
		<count></count>
	</backup-profile>
</backup-profiles>
```

## Example usage

List all available profiles:
```
backup.py
```

Start test run for profile "mydata":
```
backup.py -n --delete mydata
```

Start backup of profile named "mydata" and delete files in target directory:
```
backup.py --delete mydata
```

Start backup of profile named "mydata" and "opt". Do not delete files in target directory:
```
backup.py mydata opt
```

Use alisas to make backup even more easier: ????????????
```
alias backup.all.try='backup.py -n --delete mydata opt'
alias backup.all.run='backup.py --delete mydata opt'
```

