# -*- coding: utf-8 -*-
import configparser


class Config:
    def __init__(self, config_file):
        self.config = configparser.ConfigParser()
        self.config.read([config_file])

        self.db = _DatabaseConfig()
        self._database_to_var(self.config.items('database'))

        self.path = self.config.get('general', 'rootDir')
        self.domain = self.config.get('general', 'domain')

        self.zimbra = ZimbraAdminConfig(self.config.get('zimbra', 'login'),
                                        self.config.get('zimbra', 'password'),
                                        self.config.get('zimbra', 'url'))

    def _database_to_var(self, section):
        for item in section:
            if item[0] == 'host':
                self.db.host = item[1]
            if item[0] == 'user':
                self.db.user = item[1]
            if item[0] == 'password':
                self.db.password = item[1]
            if item[0] == 'database':
                self.db.database = item[1]

    def _special_folders_to_var(self, section):
        for item in section:
            self.special_folders[item[0]] = item[1]


class _DatabaseConfig:
    def __init__(self):
        self.host = ''
        self.user = ''
        self.password = ''
        self.database = ''


class ZimbraAdminConfig:
    def __init__(self, login: str, password: str, url: str):
        self.login = login
        self.password = password
        self.url = url
