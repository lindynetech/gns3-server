# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Reads the configuration file and store the settings for the server & modules.
"""

import sys
import os
import configparser
import asyncio

import logging
log = logging.getLogger(__name__)

CLOUD_SERVER = 'CLOUD_SERVER'


class Config(object):

    """
    Configuration file management using configparser.

    :params files: Array of configuration files (optional)
    """

    def __init__(self, files=None):

        self._files = files

        # Monitor configuration files for changes
        self._watched_files = {}

        # Override config from command line even if we modify the config file and live reload it.
        self._override_config = {}

        if sys.platform.startswith("win"):

            appname = "GNS3"

            # On windows, the configuration file location can be one of the following:
            # 1: %APPDATA%/GNS3/server.ini
            # 2: %APPDATA%/GNS3.ini
            # 3: %COMMON_APPDATA%/GNS3/server.ini
            # 4: %COMMON_APPDATA%/GNS3.ini
            # 5: server.ini in the current working directory

            appdata = os.path.expandvars("%APPDATA%")
            common_appdata = os.path.expandvars("%COMMON_APPDATA%")
            self._cloud_file = os.path.join(appdata, appname, "cloud.ini")
            filename = "server.ini"
            if self._files is None:
                self._files = [os.path.join(appdata, appname, filename),
                               os.path.join(appdata, appname + ".ini"),
                               os.path.join(common_appdata, appname, filename),
                               os.path.join(common_appdata, appname + ".ini"),
                               filename,
                               self._cloud_file]
        else:

            # On UNIX-like platforms, the configuration file location can be one of the following:
            # 1: $HOME/.config/GNS3/server.conf
            # 2: $HOME/.config/GNS3.conf
            # 3: /etc/xdg/GNS3/server.conf
            # 4: /etc/xdg/GNS3.conf
            # 5: server.conf in the current working directory

            if sys.platform.startswith("darwin"):
                appname = "gns3.net"
            else:
                appname = "GNS3"
            home = os.path.expanduser("~")
            self._cloud_file = os.path.join(home, ".config", appname, "cloud.conf")
            filename = "server.conf"
            if self._files is None:
                self._files = [os.path.join(home, ".config", appname, filename),
                               os.path.join(home, ".config", appname + ".conf"),
                               os.path.join("/etc/xdg", appname, filename),
                               os.path.join("/etc/xdg", appname + ".conf"),
                               filename,
                               self._cloud_file]

        self._config = configparser.ConfigParser()
        self.read_config()
        self._cloud_config = configparser.ConfigParser()
        self.read_cloud_config()
        self._watch_config_file()

    def _watch_config_file(self):
        asyncio.get_event_loop().call_later(1, self._check_config_file_change)

    def _check_config_file_change(self):
        """
        Check if configuration file has changed on the disk
        """

        changed = False
        for file in self._watched_files:
            try:
                if os.stat(file).st_mtime != self._watched_files[file]:
                    changed = True
            except OSError:
                continue
        if changed:
            self.read_config()
        for section in self._override_config:
            self.set_section_config(section, self._override_config[section])
        self._watch_config_file()

    def list_cloud_config_file(self):
        return self._cloud_file

    def read_cloud_config(self):
        parsed_file = self._cloud_config.read(self._cloud_file)
        if not self._cloud_config.has_section(CLOUD_SERVER):
            self._cloud_config.add_section(CLOUD_SERVER)

    def cloud_settings(self):
        return self._cloud_config[CLOUD_SERVER]

    def read_config(self):
        """
        Read the configuration files.
        """

        parsed_files = self._config.read(self._files)
        if not parsed_files:
            log.warning("No configuration file could be found or read")
        else:
            for file in parsed_files:
                log.info("Load configuration file {}".format(file))
                self._watched_files[file] = os.stat(file).st_mtime

    def get_default_section(self):
        """
        Get the default configuration section.

        :returns: configparser section
        """

        return self._config["DEFAULT"]

    def get_section_config(self, section):
        """
        Get a specific configuration section.
        Returns the default section if none can be found.

        :returns: configparser section
        """

        if section not in self._config:
            return self._config["DEFAULT"]
        return self._config[section]

    def set_section_config(self, section, content):
        """
        Set a specific configuration section. It's not
        dumped on the disk.

        :param section: Section name
        :param content: A dictionary with section content
        """

        if not self._config.has_section(section):
            self._config.add_section(section)
        for key in content:
            self._config.set(section, key, content[key])
        self._override_config[section] = content

    @staticmethod
    def instance(files=[]):
        """
        Singleton to return only on instance of Config.

        :params files: Array of configuration files (optionnal)
        :returns: instance of Config
        """

        if not hasattr(Config, "_instance"):
            Config._instance = Config()
        return Config._instance
