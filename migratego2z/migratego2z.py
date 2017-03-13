#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlalchemy
from typing import List
from typing import Dict
from migratego2z import go_db
from migratego2z.config import Config
from migratego2z.adapters import users, maildir


class Main:
    def __init__(self, mdirs: str, domain: str, config: str):
        self.users = []
        self.emailAccounts = []
        self.config = Config(config)
        if mdirs is not None:
            self.path = mdirs
        else:
            self.path = self.config.path
        if domain is not None:
            self.domain = domain
        else:
            self.domain = self.config.domain

    def main(self):
        engine = sqlalchemy.create_engine('mysql+mysqlconnector://' + self.config.db.user + ':' + self.config.db.password +
                                          '@' + self.config.db.host + '/' + self.config.db.database)
        conn = engine.connect()
        s = sqlalchemy.select([go_db.EmAccount]).where(go_db.EmAccount.username.like('%@'+self.config.domain))
        result = conn.execute(s)
        userids=[]
        for row in result:
            self.emailAccounts.append(row)
            userids.append(row.user_id)
        result.close()
        s = sqlalchemy.select([go_db.GoUser]).where(go_db.GoUser.id.in_(userids))
        result = conn.execute(s)
        for row in result:
            self.users.append(row)
        result.close()
        users_str, supp_email, supp_email_addresses = users.create_users(self.users, self.config.domain, self.config, 'user_creation')
        # print(users_str)
        print('========================================================================================================================')
        mails_str = self.import_mails(supp_email, supp_email_addresses, 'mail_copy')
        # print(mails_str)
# Dict[int, List[str]], List[int]

    def import_mails(self, supp_email: Dict[int, List[str]], supp_email_addresses: List[str], filename: str = None) \
            -> str:
        import_str = ''
        for email in self.emailAccounts:
            [user, domain] = email.username.split('@')
            prefix = None
            tmp_str = ''
            if email.username in supp_email_addresses and email.user_id in supp_email:
                sharer = email.username
                users_sup_email = supp_email[email.user_id]
                for user in users_sup_email:
                    import_str += 'selectMailbox -A ' + sharer + '\n'
                    import_str += 'modifyFolderGrant / account ' + user + ' rwixd\n'
                    import_str += 'selectMailbox -A ' + user + '\n'
                    import_str += 'createMountpoint /' + sharer + ' ' + sharer + '\n'
            else:
                import_str += 'selectMailbox -A ' + user + '@' + domain + '\n'
                import_str += tmp_str
                user_maildir = maildir.extract_folders(email, self.config.path)
                import_str += user_maildir.get_tree_creation([email.sent, email.drafts, email.trash, email.spam, '.'])
                import_str += user_maildir.get_tree_messages(email, self.config.path)

        if filename is not None:
            user_import = open(filename, 'wb')
            user_import.write(import_str.encode('utf-8'))
            user_import.close()
        return import_str

