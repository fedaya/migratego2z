#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy
from os import path
import os
import re
import shutil
from timeit import default_timer as timer
from typing import List

from migratego2z.go_db import EmAccount, AbCompany, AbContact, GoUser, AbAddressbook
from migratego2z.config import Config
from migratego2z.adapters import users, maildir, addressbook, calendar


class Main:
    def __init__(self, mdirs: str, domain: str, config: str, exclusion_list: List[str] = [None], user: str = None):
        self.users = []
        self.emailAccounts = []
        self.addressBooks = []
        self.contacts = []
        self.user = user
        self.excluded_users = exclusion_list
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

    def delete_temp_structure(self, base_name: str):
        shutil.rmtree(base_name)

    def main(self):
        start = timer()
        base_folder = self.create_temp_structure()
        print(base_folder)
        log_file = path.join(base_folder, 'import.log')
        logger = open(log_file, 'w', encoding='utf-8')
        logger.write('=' * 80 + '\n')
        logger.write('Initial steps\n')
        logger.write('=' * 80 + '\n')
        engine = sqlalchemy.create_engine('mysql+mysqlconnector://' + self.config.db.user + ':' +
                                          self.config.db.password + '@' + self.config.db.host + '/' + self.config.db.database)
        conn = engine.connect()
        if self.excluded_users != [None]:
            s = sqlalchemy.select([GoUser]).where(GoUser.username.in_(self.excluded_users))
            results = conn.execute(s)
            excluded = []
            for row in results:
                excluded.append(row.id)
            s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@' + self.config.domain)). \
                where(EmAccount.user_id.notin_(excluded))

        elif self.user is None:
            s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@'+self.config.domain))
        else:
            s = sqlalchemy.select([GoUser]).where(GoUser.username.like(self.user))
            result = conn.execute(s)
            user = []
            for row in result:
                user.append(row.id)
            s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@' + self.config.domain)).\
                where(EmAccount.user_id.in_(user))
        result = conn.execute(s)
        userids=[]
        for row in result:
            self.emailAccounts.append(row)
            if row.user_id not in userids:
                userids.append(row.user_id)
        result.close()
        s = sqlalchemy.select([GoUser]).where(GoUser.id.in_(userids))
        result = conn.execute(s)
        for row in result:
            self.users.append(row)
        result.close()


        end = timer()
        logger.write('First steps took: ' + "%.2f" % (end - start) + 's\n')
        start = timer()
        # Create the users
        users_creation_file, users_creation, \
            supp_email, supp_email_addresses = users.create_users(self.users, self.config.domain, conn, base_folder)
        end = timer()
        logger.write('User creation file generation took: ' + "%.2f" % (end - start) + 's\n')
        # Create the folders and import the mails for all users
        start = timer()
        mail_import_file, mail_import = maildir.import_mails(self.emailAccounts, supp_email, supp_email_addresses,
                                                             self.config.path, base_folder)
        end = timer()
        logger.write('Mail import generation took: ' + "%.2f" % (end - start) + 's\n')
        # Create the folders and imports the contacts
        start = timer()
        addressbooks_import_file, addressbooks_import = self.import_addressbooks(conn, base_folder)
        end = timer()
        logger.write('Addressbooks import generation took: ' + "%.2f" % (end - start) + 's\n')
        start = timer()
        calendars_import_file, calendars_import = self.import_calendars(conn, base_folder)
        end = timer()
        logger.write('Calendars import generation took: ' + "%.2f" % (end - start)  + 's\n')
        conn.close()
        start = timer()
        script_file, script = self.generate_script(users_creation_file, mail_import_file,
                                                   addressbooks_import_file, calendars_import_file, base_folder,
                                                   log_file)
        end = timer()
        logger.write('Script creation took : ' + "%.2f" % (end - start) + 's\n')
        logger.write('=' * 80 + '\n')
        logger.write('End of initial steps\n')
        logger.write('=' * 80 + '\n\n')
        logger.close()

    def import_addressbooks(self, conn: sqlalchemy.engine.Connection, base_folder: str) -> (str, str):
        addressbooks_file = (open(path.join(base_folder, 'contacts_copy.zmm'), 'w', encoding='utf-8'),
                             open(path.join(base_folder, 'contacts_copy.sh'), 'w', encoding='utf-8'))
        addressbooks_zimbra = ''
        addressbooks_script = '#!/bin/sh\n'
        for user in self.emailAccounts:
            s = sqlalchemy.select([AbAddressbook]).where(AbAddressbook.user_id == user.user_id)
            result = conn.execute(s)
            for row in result:
                s2 = sqlalchemy.select([AbContact, AbCompany.name], AbContact.addressbook_id == row.id,
                                       AbContact.__table__.outerjoin(AbCompany, AbContact.company_id == AbCompany.id))
                r2 = conn.execute(s2)
                line = addressbook.generate_vcf(r2, path.join(base_folder, 'contacts', 'contacts'),
                                                row.name, user.username, self.config.zimbra)
                addressbooks_zimbra += line[0]
                addressbooks_script += line[1]
                r2.close()
            result.close()
        addressbooks_file[0].write(addressbooks_zimbra)
        addressbooks_file[0].close()
        addressbooks_file[1].write(addressbooks_script)
        addressbooks_file[1].close()
        os.chmod(path.join(base_folder, 'contacts_copy.sh'), 0o777)
        return ('contacts_copy.zmm', 'contacts_copy.sh'), (addressbooks_zimbra, addressbooks_script)

    def import_calendars(self, conn: sqlalchemy.engine.Connection, base_folder: str) -> (str, str):
        calendars_file = (open(path.join(base_folder, 'calendars_copy.zmm'), 'w', encoding='utf-8'),
                          open(path.join(base_folder, 'calendars_copy.sh'), 'w', encoding='utf-8'))

        calendars_zimbra = ''
        calendars_script = '#!/bin/sh\n'
        for user in self.emailAccounts:
            line = calendar.export_calendars_from_user(conn, user, os.path.join(base_folder, 'calendars',
                                                                                          'calendars'),
                                                       self.config.zimbra)
            calendars_zimbra += line[0]
            calendars_script += line[1]
        # calendars_file.write(calendars_str.encode('utf-8'))
        calendars_file[0].write(calendars_zimbra)
        calendars_file[0].close()
        calendars_file[1].write(calendars_script)
        calendars_file[1].close()
        os.chmod(path.join(base_folder, 'calendars_copy.sh'), 0o777)
        return ('calendars_copy.zmm', 'calendars_copy.sh'), (calendars_zimbra, calendars_script)

    def generate_script(self, users_creation: str, mail_import: str, addressbooks_import: (str, str),
                        calendars_import: (str, str), base_folder: str, log_file: str) -> (str, str):
        zmprov = "/usr/bin/time /opt/zimbra/bin/zmprov -v -z -f {file}"
        zmmailbox = "/usr/bin/time /opt/zimbra/bin/zmmailbox -v -z -f {file}"
        bash = "/usr/bin/time ./{file}"
        deco = '=' * 80 + '\n{desc}\n' + '=' * 80
        deco2 = '-' * 80 + '\n{desc}\n' + '-' * 80
        eol = ' >> ' + log_file + ' 2>&1\n'
        script = "#!/bin/sh\n"
        script += 'echo "' + re.sub(r'\{desc\}', "User creation", deco) + '"' + eol
        script += re.sub(r'\{file\}', users_creation, zmprov) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "End of user creation", deco) + '\n' + '"' + eol
        script += 'echo "' + re.sub(r'\{desc\}', "Mail import", deco) + '"' + eol
        for file in mail_import:
            script += re.sub(r'\{file\}', file, zmmailbox) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "End of mail import", deco) + '\n' + '"' + eol
        script += 'echo "' + re.sub(r'\{desc\}', "Addressbooks import", deco) + '"' + eol
        script += 'echo "' + re.sub(r'\{desc\}', "- Creating Folders", deco2) + '"' + eol
        script += re.sub(r'\{file\}', addressbooks_import[0], zmmailbox) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "- Importing ics files", deco2) + '"' + eol
        script += re.sub(r'\{file\}', addressbooks_import[1], bash) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "End of addressbooks import", deco) + '\n' + '"' + eol
        script += 'echo "' + re.sub(r'\{desc\}', "Calendars import", deco) + '"' + eol
        script += 'echo "' + re.sub(r'\{desc\}', "- Creating Folders", deco2) + '"' + eol
        script += re.sub(r'\{file\}', calendars_import[0], zmmailbox) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "- Importing vcf files", deco2) + '"' + eol
        script += re.sub(r'\{file\}', calendars_import[1], bash) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "End of calendars import", deco) + '\n' + '"' + eol
        script += 'echo "' + re.sub(r'\{desc\}', "That's all, folks!", deco) + '"' + eol
        script_name = path.join(base_folder, 'migratego2z.sh')
        script_file = open(script_name, 'w', encoding='utf-8')
        # script_file.write(script.encode('utf-8'))
        script_file.write(script)
        script_file.close()
        os.chmod(script_name, 0o777)
        return script_name, script


