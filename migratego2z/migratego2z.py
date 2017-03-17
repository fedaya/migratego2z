#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy
from os import path
import os
import shutil

from migratego2z.go_db import EmAccount, AbCompany, AbContact, GoUser, AbAddressbook
from migratego2z.config import Config
from migratego2z.adapters import users, maildir, addressbook, calendar


class Main:
    def __init__(self, mdirs: str, domain: str, config: str):
        self.users = []
        self.emailAccounts = []
        self.addressBooks = []
        self.contacts = []
        self.config = Config(config)
        if mdirs is not None:
            self.path = mdirs
        else:
            self.path = self.config.path
        if domain is not None:
            self.domain = domain
        else:
            self.domain = self.config.domain
    def create_temp_structure(self) -> str:
        base_name = '/tmp/migratego2z'
        i = 0
        while path.exists(base_name + str(i)):
            i += 1
        base_name += str(i)
        os.mkdir(base_name)
        os.mkdir(path.join(base_name, 'contacts'))
        os.mkdir(path.join(base_name, 'calendars'))
        return base_name

    def delete_temp_structure(self, base_name:str):
        shutil.rmtree(base_name)

    def main(self):
        engine = sqlalchemy.create_engine('mysql+mysqlconnector://' + self.config.db.user + ':' + self.config.db.password +
                                          '@' + self.config.db.host + '/' + self.config.db.database)
        conn = engine.connect()
        s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@'+self.config.domain))
        result = conn.execute(s)
        userids=[]
        for row in result:
            self.emailAccounts.append(row)
            userids.append(row.user_id)
        result.close()
        s = sqlalchemy.select([GoUser]).where(GoUser.id.in_(userids))
        result = conn.execute(s)
        for row in result:
            self.users.append(row)
        result.close()
        # Create the users
        base_folder = self.create_temp_structure()
        users_str, supp_email, supp_email_addresses = users.create_users(self.users, self.config.domain, self.config,
                                                                         path.join(base_folder, 'user_creation'))
        # Create the folders and import the mails for all users
        mails_str = maildir.import_mails(self.emailAccounts, supp_email, supp_email_addresses,
                                      self.config.path, path.join(base_folder, 'mail_copy'))
        # Create the folders and imports the contacts
        addressbooks_str = self.import_addressbooks(conn, base_folder)
        calendar_str = self.import_calendars(conn, base_folder)
        conn.close()

    def import_addressbooks(self, conn: sqlalchemy.engine.Connection, base_folder:str) -> str:
        addressbooks_file = open(path.join(base_folder, 'contacts_copy'), 'wb')
        addressbooks_str = ''
        for user in self.emailAccounts:
            s = sqlalchemy.select([AbAddressbook]).where(AbAddressbook.user_id == user.user_id)
            result = conn.execute(s)
            for row in result:
                s2 = sqlalchemy.select([AbContact, AbCompany.name], AbContact.addressbook_id == row.id,
                                       AbContact.__table__.outerjoin(AbCompany, AbContact.company_id == AbCompany.id))
                r2 = conn.execute(s2)
                addressbooks_str += addressbook.generate_vcf(r2, path.join(base_folder, 'contacts', 'contacts'),
                                                             row.name, user.username)
                r2.close()
            result.close()
        addressbooks_file.write(addressbooks_str.encode('utf-8'))
        addressbooks_file.close()
        return addressbooks_str

    def import_calendars(self, conn: sqlalchemy.engine.Connection, base_folder: str) -> str:
        calendars_file = open(path.join(base_folder, 'calendars_copy'), 'wb')
        calendars_str = ''
        for user in self.emailAccounts:
            calendars_str += calendar.export_calendars_from_user(conn, user, os.path.join(base_folder, 'calendars',
                                                                                          'calendars'))
        calendars_file.write(calendars_str.encode('utf-8'))
        calendars_file.close()
        return calendars_str


