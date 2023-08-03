#!/usr/bin/env python3

import logging
import os
import subprocess
import sys

def execute_command(cmd, shell=False, verbose=False, simulate=False, ignoreError=False, stdout=None, stderr=None):
    """Executes the given command."""
    if verbose or simulate:
        print(_cmd_to_str(cmd))
    if simulate:
        return None

    # flush stdout to keep output synchronized
    sys.stdout.flush()
        
    logging.debug("Command: " + _cmd_to_str(cmd))
    p = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr, universal_newlines=True)
    p.wait()
    if not ignoreError and p.poll() != 0:
        raise Exception("Command failed: " + " ".join(cmd))
    return p

def _cmd_to_str(cmd):
    """Converts a command to string."""
    if isinstance(cmd, str):
        return cmd
    cmdStr = ""
    for c in cmd:
        # add quotes if parameter contains a space
        if " " in c:
            cmdStr += "\"" + c + "\" "
        else:
            cmdStr += c + " "
    cmdStr = cmdStr.strip()
    return cmdStr

