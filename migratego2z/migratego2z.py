#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy
from os import path
import os
import re
import shutil
from timeit import default_timer as timer
from typing import List

from migratego2z.go_db import EmAccount, AbCompany, AbContact, GoUser, AbAddressbook, GoAcl, PaAlias, GoUsersGroup, GoGroup
from migratego2z.config import Config
from migratego2z.adapters import users, maildir, addressbook, calendar


class Main:
    def __init__(self, mdirs: str, domain: str, config: str, exclusion_list: List[str] = [None], user: str = None):
        self.users = []
        self.emailAccounts = []
        self.aliases = []
        self.shares = []
        self.addressBooks = []
        self.contacts = []
        self.user = user
        self.users_groups = {}
        self.groups_users = {}
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
        log_file = path.join(base_folder, 'import.log')
        logger = open(log_file, 'w', encoding='utf-8')
        logger.write('=' * 80 + '\n')
        logger.write('Initial steps\n')
        logger.write('=' * 80 + '\n')
        engine = sqlalchemy.create_engine('mysql+mysqlconnector://' + self.config.db.user + ':' +
                                          self.config.db.password + '@' + self.config.db.host + '/' + self.config.db.database)
        conn = engine.connect()
        if self.excluded_users != [None]:
            # First let's get the list of excluded users ids
            s = sqlalchemy.select([GoUser]).where(GoUser.username.in_(self.excluded_users))
            results = conn.execute(s)
            excluded = []
            for row in results:
                excluded.append(row.id)
            # The we get the EmAccount for the domain of not excluded users
            s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@' + self.config.domain)). \
                where(EmAccount.user_id.notin_(excluded))

        elif self.user is None:
            # If there is no user mentioned and no user excluded
            s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@'+self.config.domain))
        else:
            # Else, we get the user_id of the mentioned user
            s = sqlalchemy.select([GoUser]).where(GoUser.username.like(self.user))
            result = conn.execute(s)
            user_id = []
            for row in result:
                user_id.append(row.id)
            # And the corresponding EmAccount records
            s = sqlalchemy.select([EmAccount]).where(EmAccount.username.like('%@' + self.config.domain)).\
                where(EmAccount.user_id.in_(user_id))
        # Once we have the right select statement, we execute it
        result = conn.execute(s)
        userids=[]
        for row in result:
            # We add every e-mail account in self.emailAccounts
            self.emailAccounts.append(row)
            if row.user_id not in userids:
                # And the whole list of distinct user_id
                userids.append(row.user_id)
        result.close()
        # We query the database for all the users, and put them in self.users
        s = sqlalchemy.select([GoUser]).where(GoUser.id.in_(userids)).where(GoUser.enabled == 1)
        result = conn.execute(s)
        for row in result:
            self.users.append(row)
        result.close()

        # Associate groups and users and vice-versa
        s = sqlalchemy.select([GoUsersGroup]).\
            where(GoUsersGroup.user_id.in_(userids))
        result = conn.execute(s)
        for row in result:
            if row.user_id in self.users_groups:
                self.users_groups[row.user_id].append(row.group_id)
            else:
                self.users_groups[row.user_id] = [row.group_id]
        result.close()

        # Query the database for active aliases that are not reflective
        s = sqlalchemy.select([PaAlias]). \
            where(PaAlias.address.like('%@' + self.config.domain)). \
            where(PaAlias.goto.like('%@' + self.config.domain)). \
            where(PaAlias.address != PaAlias.goto). \
            where(PaAlias.active == u'1')
        result = conn.execute(s)
        for alias in result:
            self.aliases.append(alias)
        result.close()

        # The shares are made with the GoAcl. EmAccount has an acl_id, GoAcl has a user_id.
        # We search for these acl, if the EmAccount.user_id is not the same as the GoUser.id. Those are the shares.
        # The is one other method for sharing, that is creating another EmAccount for the GoUser;
        # this is implemented in maildir.import_mails.
        s = sqlalchemy.select([GoUser.username, EmAccount.username]).select_from(
            EmAccount.__table__.join(GoAcl.__table__, EmAccount.acl_id == GoAcl.acl_id).join(GoUser.__table__, GoUser.id == GoAcl.user_id)).where(
            GoAcl.level > 10).where(GoUser.id.in_(userids)).where(GoUser.id != EmAccount.user_id).where(GoUser.enabled == 1)
        result = conn.execute(s)
        for row in result:
            share = {'user': row[0], 'email': row[1]}
            self.shares.append(share)
        result.close()

        end = timer()
        logger.write('First steps took: ' + "%.2f" % (end - start) + 's\n')

        start = timer()
        # Create the users
        users_creation_file, users_creation, \
            supp_email, supp_email_addresses = users.create_users(self.users, self.aliases, self.config.domain, conn, base_folder)
        end = timer()
        logger.write('User and Aliases creation file generation took: ' + "%.2f" % (end - start) + 's\n')
        # Create the folders and import the mails for all users
        start = timer()
        mail_import_file, mail_import = maildir.import_mails(self.emailAccounts, supp_email, supp_email_addresses,
                                                             self.config.path, base_folder)
        end = timer()
        logger.write('Mail import generation took: ' + "%.2f" % (end - start) + 's\n')
        start = timer()
        mail_share_file, mail_share, sendas_file, sendas = maildir.import_shares(self.shares, base_folder,
                                                                                 self.config.domain)
        # Insert the mailbox shares before the folders creation
        mail_import_file.insert(0, mail_share_file)
        end = timer()
        logger.write('Mailbox shares import generation took: ' + "%.2f" % (end - start) + 's\n')
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
        domain_state_change = self.change_domain_states(base_folder)
        end = timer()
        logger.write('Domain states change generation took: ' + "%.2f" % (end - start) + 's\n')

        start = timer()
        script_file, script = self.generate_script(users_creation_file, sendas_file, mail_import_file,
                                                   addressbooks_import_file, calendars_import_file, domain_state_change,
                                                   base_folder, log_file)
        launch_script = self.generate_launch_script(base_folder, script_file, log_file)
        end = timer()
        logger.write('Script creation took : ' + "%.2f" % (end - start) + 's\n')
        logger.write('=' * 80 + '\n')
        logger.write('End of initial steps\n')
        logger.write('=' * 80 + '\n\n')
        logger.close()
        print('Migration scripts have been successfully created.')

        exec_pbs, exec_str = self.race_conditions()
        if not exec_pbs == 0:
            if exec_pbs > 1:
                print('Before launching the migration resolve these ' + str(exec_pbs) + ' problems:')
            else:
                print('Before launching the migration resolve this problem:')
            print(exec_str)
        else:
            print('Everything is set for the migration.\n')
        print('You can launch the migration with the command: ' + launch_script)

    def import_addressbooks(self, conn: sqlalchemy.engine.Connection, base_folder: str) -> (str, str):
        addressbooks_file = (open(path.join(base_folder, 'contacts_copy.zmm'), 'w', encoding='utf-8'),
                             open(path.join(base_folder, 'contacts_copy.sh'), 'w', encoding='utf-8'))
        addressbooks_zimbra = ''
        addressbooks_script = '#!/bin/sh\n'
        for user in self.users:
            s = sqlalchemy.select([AbAddressbook]).where(AbAddressbook.user_id == user.id)
            result = conn.execute(s)
            for row in result:
                s2 = sqlalchemy.select([AbContact, AbCompany.name], AbContact.addressbook_id == row.id,
                                       AbContact.__table__.outerjoin(AbCompany, AbContact.company_id == AbCompany.id))
                r2 = conn.execute(s2)
                line = addressbook.generate_vcf(r2, path.join(base_folder, 'contacts', 'contacts'),
                                                row.name, user, self.config)
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
        for user in self.users:
            line = calendar.export_calendars_from_user(conn, user, os.path.join(base_folder, 'calendars',
                                                                                          'calendars'),
                                                       self.config, self.users_groups[user.id])
            calendars_zimbra += line[0]
            calendars_script += line[1]
        # calendars_file.write(calendars_str.encode('utf-8'))
        calendars_file[0].write(calendars_zimbra)
        calendars_file[0].close()
        calendars_file[1].write(calendars_script)
        calendars_file[1].close()
        os.chmod(path.join(base_folder, 'calendars_copy.sh'), 0o777)
        return ('calendars_copy.zmm', 'calendars_copy.sh'), (calendars_zimbra, calendars_script)

    def generate_script(self, users_creation: str, sendas: str, mail_import: str, addressbooks_import: (str, str),
                        calendars_import: (str, str), domain_state_change: str, base_folder: str,
                        log_file: str) -> (str, str):
        zmprov = "/usr/bin/time /opt/zimbra/bin/zmprov -v -z -f {file}"
        zmmailbox = "/usr/bin/time /opt/zimbra/bin/zmmailbox -v -z -f {file}"
        bash = "/usr/bin/time ./{file}"
        deco = '=' * 80 + '\n{desc}\n' + '=' * 80
        deco2 = '-' * 80 + '\n{desc}\n' + '-' * 80
        eol = ' >> ' + log_file + ' 2>&1\n'
        script = "#!/bin/sh\n"
        script += 'echo "' + re.sub(r'\{desc\}', "User creation", deco) + '"' + eol
        script += re.sub(r'\{file\}', users_creation, zmprov) + eol
        script += re.sub(r'\{file\}', sendas, zmprov) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "End of user creation", deco) + '\n' + '"' + eol

        # script += 'echo "' + re.sub(r'\{desc\}', "Please Reroute the e-mails now before going further", deco) + '"\n'
        # script += 'echo "' + re.sub(r'\{desc\}', 'Press any key to continue...', deco) + '"\n'
        # script += 'read a\n'

        script += 'echo "' + re.sub(r'\{desc\}', "Changing the domain states on both servers", deco) + '"' + eol
        script += re.sub(r'\{file\}', domain_state_change, bash) + eol
        script += 'echo "' + re.sub(r'\{desc\}', "Domain states should be changed on the servers",
                                    deco) + '\n' + '"' + eol

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

    def change_domain_states(self, base_folder):
        query = 'UPDATE pa_domains SET active=0 WHERE domain=\'' + self.config.domain + '\'\n'
        sql_name = path.join(base_folder, 'deactivate_domain.sql')
        sql_file = open(sql_name, 'w', encoding='utf-8')
        sql_file.write(query)
        sql_file.close()

        db = self.config.db
        zmprov = "/usr/bin/time /opt/zimbra/bin/zmprov -v -z -f {file}"

        domain = self.config.domain
        md_script  = 'md ' + domain + 'zimbraMailCatchAllAddress ""\n'
        md_script += 'md ' + domain + 'zimbraMailCatchAllForwardingAddress ""\n'
        md_script += 'md ' + domain + 'zimbraMailTransport lmtp:' + self.config.zimbra.server + ':7025\n'

        md_name = path.join(base_folder, 'disable_relaying.zmp')
        md_file = open(md_name, 'w', encoding='utf-8')
        md_file.write(md_script)
        md_file.close()

        script = '#!/bin/sh\n'

        script += '/usr/bin/mysql --host=' + db.host + ' --user=' + db.user + ' --password=' + db.password + \
                  ' --database=' + db.database + r' --force <' + sql_name + '\n'
        script += r'ssh root@' + self.config.goserver + ' "/etc/init.d/postfix reload"' + '\n'
        script += re.sub(r'\{file\}', md_name, zmprov) + '\n'
        script_name = path.join(base_folder, 'change_domain_states.sh')
        script_file = open(script_name, 'w', encoding='utf-8')
        script_file.write(script)
        script_file.close()

        return 'change_domain_states.sh'


    def generate_launch_script(self, base_folder, migrate_script, log_file):
        script  = '#!/bin/sh\n'
        script += 'echo This script will launch the migration as a daemon and display the log file as it grows\n'
        script += 'echo Press any key to start or Ctrl+C to cancel...\n'
        script += 'read a\n'
        script += '/usr/bin/screen -dmS migratego2z ' + migrate_script +'\n'
        script += '/usr/bin/tail -f ' + log_file +'\n'

        script_name = path.join(base_folder, 'launch.sh')
        script_file = open(script_name, 'w', encoding='utf-8')
        script_file.write(script)
        script_file.close()

        return script_name

    def race_conditions(self):
        executables = [
            '/bin/sh',
            '/usr/bin/mysql',
            '/usr/bin/curl',
            '/usr/bin/ssh',
            '/usr/bin/screen',
            '/usr/bin/time',
            '/opt/zimbra/bin/zmprov',
            '/opt/zimbra/bin/zmmailbox'
        ]
        return_string = ''
        return_pbs = 0
        for executable in executables:
            if not (path.exists(executable) and os.access(executable, os.X_OK)):
                return_string += ' - ' + executable + ' doesn\'t exist or is not executable\n'
                return_pbs += 1
        return return_pbs, return_string

        print('Please make sure:')
        print(' 1 - You run this migration on a Zimbra server')
        print(' 2 - Zimbra is installed on the default path: /opt/zimbra')
        print(' 3 - ssh is available and you can login on Group-Office\'s server as root without password')
        print(' 4 - mysql client is available in /usr/bin')
        print(' 5 - time utility is available in /usr/bin')
        print(' 6 - sh is available in /bin')
        print(' 7 - screen is available in /usr/bin')
        print(' 8 - curl is available in /usr/bin')



