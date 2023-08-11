#!/usr/bin/env python3

import unittest
import os
import sys
import shutil
import datetime
from unittest import mock
from unittest import TestCase

# import from parent dir
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PROJECT_DIR))
import backup
ROOT_DIR = os.path.join(PROJECT_DIR, 'root')
SRC_1_DIR = os.path.join(ROOT_DIR, 'src-1')
DST_1_DIR = os.path.join(ROOT_DIR, 'dst-1')
TEST_XML = os.path.join(PROJECT_DIR, 'backup-test.xml')
TEST_ERROR_XML = os.path.join(PROJECT_DIR, 'backup-test-error.xml')
PROFILE_SYNC = 'sync'
PROFILE_SYNC_EXCLUDE = 'sync-exclude'
PROFILE_INCR = 'incr'

# Usage:
# > test_backup.py
# > test_backup.py TestBackup.test_remove_unmanaged_forced

class TestBackup(unittest.TestCase):
    def setUp(self):
        os.makedirs(ROOT_DIR, exist_ok=True)
        shutil.rmtree(ROOT_DIR)
        
        os.makedirs(SRC_1_DIR, exist_ok=True)
        os.makedirs(DST_1_DIR, exist_ok=True)
   
    def test_xmlfile_default(self):
        print('======= test_xmlfile_default ===')
        with self.assertRaises(SystemExit) as cm:
            backup.main(['--debug', '-p'])
        self.assertEqual(cm.exception.code, 0)
    def test_xmlfile_relative(self):
        print('======= test_xmlfile_relative ===')
        with self.assertRaises(SystemExit) as cm:
            backup.main(['--debug', '--file', 'backup-test.xml', '-p'])
        self.assertEqual(cm.exception.code, 0)
        with self.assertRaises(SystemExit) as cm:
            backup.main(['--debug', '--file', 'backup-test.xml', '-p', 'sync', 'incr'])
        self.assertEqual(cm.exception.code, 0)
    def test_xmlfile_absolute(self):
        print('======= test_xmlfile_absolute ===')
        with self.assertRaises(SystemExit) as cm:
            backup.main(['--debug', '--file', TEST_XML, '-p'])
        self.assertEqual(cm.exception.code, 0)
    def test_xmlfile_validate(self):
        print('======= test_xmlfile_validate ===')
        with self.assertRaises(SystemExit) as cm:
            backup.main(['--debug', '--file', TEST_ERROR_XML, '-p'])
        self.assertEqual(cm.exception.code, 1)

    def test_sync_dryrun(self):
        print('======= test_sync_dryrun ===')
        self._createFiles(SRC_1_DIR, 5)
        backup.main(['--debug', '--file', TEST_XML, '-n', PROFILE_SYNC])
        self.assertEqual(len(os.listdir(DST_1_DIR)), 0)
    def test_sync(self):
        print('======= test_sync ===')
        self._createFiles(SRC_1_DIR, 5)
        backup.main(['--debug', '--file', TEST_XML, PROFILE_SYNC])
        self.assertEqual(len(os.listdir(DST_1_DIR)), 5)
    def test_sync_exclude(self):
        print('======= test_sync_exclude ===')
        self._createFiles(SRC_1_DIR, 5)
        backup.main(['--debug', '--file', TEST_XML, PROFILE_SYNC_EXCLUDE])
        self.assertEqual(len(os.listdir(DST_1_DIR)), 4)
    def test_sync_delete(self):
        print('======= test_sync_delete ===')
        self._createFiles(SRC_1_DIR, 5)
        self._createFiles(DST_1_DIR, 7, 'deleteme')
        backup.main(['--debug', '--file', TEST_XML, '--delete', PROFILE_SYNC])
        self.assertEqual(len(os.listdir(DST_1_DIR)), 5)
    
    def test_incr(self):
        print('======= test_incr ===')
        self._createFiles(SRC_1_DIR, 5)
        backup.main(['--debug', '--file', TEST_XML, PROFILE_INCR])
        self.assertEqual(len(os.listdir(DST_1_DIR)), 1)
        TARGET_FOLDER = os.path.join(DST_1_DIR, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.assertEqual(len(os.listdir(TARGET_FOLDER)), 5)
        self.assertTrue(os.path.exists(os.path.join(TARGET_FOLDER, 'file-1.txt')))
    def test_incr_dryrun(self):
        print('======= test_incr_dryrun ===')
        self._createFiles(SRC_1_DIR, 5)
        folder2000 = os.path.join(DST_1_DIR, '2000-03-12')
        folder2010 = os.path.join(DST_1_DIR, '2010-03-12')
        folder2020 = os.path.join(DST_1_DIR, '2020-03-12')
        os.makedirs(folder2000, exist_ok=True)
        os.makedirs(folder2010, exist_ok=True)
        os.makedirs(folder2020, exist_ok=True)
        backup.main(['--debug', '--file', TEST_XML, '-n', PROFILE_INCR])
        self.assertTrue(os.path.exists(folder2000), msg=f'{folder2000}')
        self.assertTrue(os.path.exists(folder2010), msg=f'{folder2010}')
        self.assertTrue(os.path.exists(folder2020), msg=f'{folder2020}')
        TARGET_FOLDER = os.path.join(DST_1_DIR, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.assertFalse(os.path.exists(TARGET_FOLDER), msg=f'{TARGET_FOLDER}')
    def test_incr_folders(self):
        print('======= test_incr_folders ===')
        self._createFiles(SRC_1_DIR, 5)
        folder2000 = os.path.join(DST_1_DIR, '2000-03-12')
        folder2010 = os.path.join(DST_1_DIR, '2010-03-12')
        folder2020 = os.path.join(DST_1_DIR, '2020-03-12')
        os.makedirs(folder2000, exist_ok=True)
        os.makedirs(folder2010, exist_ok=True)
        os.makedirs(folder2020, exist_ok=True)
        backup.main(['--debug', '-v', '--file', TEST_XML, PROFILE_INCR])
        TARGET_FOLDER = os.path.join(DST_1_DIR, datetime.datetime.now().strftime("%Y-%m-%d"))
        # only one folder is deleted for each execution
        self.assertFalse(os.path.exists(folder2000), msg=f'{folder2000}')
        self.assertTrue(os.path.exists(folder2010), msg=f'{folder2010}')
        self.assertTrue(os.path.exists(folder2020), msg=f'{folder2020}')
        self.assertTrue(os.path.exists(TARGET_FOLDER), msg=f'{TARGET_FOLDER}')
        self.assertEqual(len(os.listdir(DST_1_DIR)), 3)
        self.assertEqual(len(os.listdir(TARGET_FOLDER)), 5)
        self.assertTrue(os.path.exists(os.path.join(TARGET_FOLDER, 'file-1.txt')))
        # run again -> delete another folder
        backup.main(['--debug', '-v', '--file', TEST_XML, PROFILE_INCR])
        self.assertFalse(os.path.exists(folder2010), msg=f'{folder2010}')
        self.assertEqual(len(os.listdir(DST_1_DIR)), 2)

    @mock.patch('backup.input', create=True)
    def test_restore_sync(self, mocked_input):
        print('======= test_restore_sync ===')
        mocked_input.side_effect = ['y']
        
        self._createFiles(SRC_1_DIR, 5)
        self._createFiles(DST_1_DIR, 7)
        backup.main(['--debug', '--file', TEST_XML, '--restore', PROFILE_SYNC])
        self.assertEqual(len(os.listdir(SRC_1_DIR)), 7)
        self.assertEqual(len(os.listdir(DST_1_DIR)), 7)
    @mock.patch('backup.input', create=True)
    def test_restore_incr_restoreDate(self, mocked_input):
        print('======= test_restore_incr_restoreDate ===')
        mocked_input.side_effect = ['y', 'y']
        
        folder2010 = os.path.join(DST_1_DIR, '2010-03-12')
        folder2020 = os.path.join(DST_1_DIR, '2020-03-12')
        os.makedirs(folder2010, exist_ok=True)
        os.makedirs(folder2020, exist_ok=True)
        self._createFiles(folder2010, 10, '2010')
        self._createFiles(folder2020, 20, '2020')
        # restore 2010
        backup.main(['--debug', '--file', TEST_XML, '--restore', '--restore-date', '2010-03-12', PROFILE_INCR])
        self.assertEqual(len(os.listdir(SRC_1_DIR)), 10)
        self.assertTrue(os.path.exists(os.path.join(SRC_1_DIR, '2010-10.txt')))
        ##
        # restore 2020
        backup.main(['--debug', '--file', TEST_XML, '--restore', '--restore-date', '2020-03-12', '--delete', PROFILE_INCR])
        self.assertEqual(len(os.listdir(SRC_1_DIR)), 20)
        self.assertTrue(os.path.exists(os.path.join(SRC_1_DIR, '2020-20.txt')))

    def test_clean(self):
        print('======= test_clean ===')
        shutil.rmtree(ROOT_DIR)
    
    # Helper methods
    def _createFiles(self, dir, numberFiles=1, prefix='file'):
        os.makedirs(dir, exist_ok=True)
        for i in range(0, numberFiles):
            fileName = os.path.join(dir, f'{prefix}-{i+1}.txt')
            with open(fileName, 'x') as f:
                pass
            

if __name__ == '__main__':
    unittest.main()
    
