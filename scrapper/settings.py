# -*- coding: utf-8 -*-

import os

# VRS Settings

vrs = {}
vrs['username'] = "user"
vrs['password'] = 'pass'

# Proxy settings
PROXY = "fw_in.bnf.fr:8080"

# Directories settings
script_dir = os.path.dirname(os.path.realpath(__file__))
download_dir = os.path.join(script_dir, "downloads")
log_dir = os.path.join(script_dir, "logs")
gecko_log_path = os.path.join(log_dir, "geckodriver.log")