import configparser as cp

"""
This module is responsible for extracting configuration / environmental settings from the configuration file.

Attributes:
-----------
    config (ConfigParser): an instance of the ConfigParser class, which is used for parsing the "config.ini" file
    to get the config settings

    DATABASE_PATH: holds the path of the database, from the config.ini file under the 'DATABASE' section.
"""

config = cp.ConfigParser()
config.read('config.ini')
DATABASE_PATH = config.get('DATABASE', 'path')
