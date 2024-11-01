# Backup.py

Backup.py is your solution to backup your data!

Backup.py provides the following features:
- Support for incremental backups: only back up data that has changed since the previous backup
- Optimize memory usage: Avoid to store the same file several times
- Define backup profiles once: Use these profiles for your regular backup tasks
- Easy to use: several profiles can be executed with a single command

## Install
1. Install Python3 as follows in Ubuntu/Debian Linux:
```
sudo apt install python3.6
```

2. Install external applications:
```
sudo apt install rsync
```

3. Download Backup.py and set execute permissions:
```
curl -LJO https://raw.githubusercontent.com/byte-cook/backup/main/backup.py
curl -LJO https://raw.githubusercontent.com/byte-cook/backup/main/osutil.py
curl -LJO https://raw.githubusercontent.com/byte-cook/backup/main/xmlutil.py
chmod +x backup.py 
```

4. (Optional) Use opt.py to install it to the /opt directory:
```
sudo opt.py install backup backup.py osutil.py xmlutil.py
```

## Profile definiton

Define your backup profile in the definition file "backup.xml". By default, this file is searched in the same folder as backup.py.

You can create an example definition file with this command:
```
backup.py -t > backup.xml
```
The XML structure is as follows:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<backup-profiles>
	<backup-profile>
		<name>home2nas</name>
		<description>home directory to NAS</description>
		<source>/home/user</source>
		<target>/mnt/nas/user/backup-home</target>
		<mode>incremental</mode>
		<option>-rltvzi</option>
		<!-- add more rsync options here -->
		<count>2</count>
	</backup-profile>
	<backup-profile>
		<name>opt2nas</name>
		<description>/opt to NAS</description>
		<source>/opt</source>
		<target>/mnt/nas/user/backup-opt</target>
		<mode>synchronize</mode>
	</backup-profile>
</backup-profiles>
```

## Example usage

List all available profiles:
```
backup.py 
```
List profiles details for "home2nas":
```
backup.py -p home2nas
```

Start test run for profile "home2nas":
```
backup.py -n --delete home2nas
```

Start backup of profile named "home2nas" and delete files in target directory if they do not exist in the source:
```
backup.py --delete home2nas
```

Start backup of profile named "home2nas" and "opt2nas". Do not delete files in target directory:
```
backup.py home2nas opt2nas
```

Use alisas to make backup even more easier: 
```
alias backup.homeopt2nas.try='backup.py -n --delete home2nas opt2nas'
alias backup.homeopt2nas.run='backup.py --delete home2nas opt2nas'
```

