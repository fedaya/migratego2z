#!/usr/bin/env python
# -*- coding: utf-8 -*-


# This script is intended to prepare a migration from maildirs to Zimbra

import os
import subprocess
import ConfigParser
import sqlalchemy
import go_db.py




class Main:
    zmmbox = '/opt/zimbra/bin/zmmailbox -z -m {USERNAME}@{DOMAIN}'
    zmprov = '/opt/zimbra/bin/zmprov'

    def __init__(self, mdirs, domain, config):
        self.users = []

        self.config = Config()
        if mdirs is not None:
            self.path = mdirs
        else:
            self.path = self.config.path
        if domain is not None:
            self.domain = domain
        else:
            self.domain = self.config.domain


    def extract_users(self):
        dir_list = os.listdir(self.path)
        for entry in dir_list:
            #print entry
            if os.path.isdir(os.path.join(self.path, entry)):
                user = User(os.path.basename(entry), self.domain)
                self.users.append(user)

    def create_users(self):
        user_creation = open('user_creation','wb')
        car = '#'
        for x in range(80):
            car+='#'
        print '\n' + car
        print '# file: user_creation'
        print car
        for user in self.users:
            user_creation.write(user.get_creation_string().encode('utf-8'))
        user_creation.close()

    def import_mails(self):

        for user in self.users:
            car = '#'
            for x in range(80):
                car += '#'
            print '\n'+car
            print '# file: user_file.'+user.user_name
            print car
            user_file = open('user_file.'+user.user_name,'wb')
            user_file.write(user.mail_dir.get_tree_creation().encode('utf-8'))
            #user_file.write(user.mail_dir.get_tree_messages(os.path.join(self.path,user.user_name)).encode('utf-8'))
            user_file.close()
            zmmboxproc = self.zmmbox.replace('{USERNAME}',user.user_name).replace('{DOMAIN}',self.domain)+ ' -f user_file.'+user.user_name
            print zmmboxproc
            zmmboxproc = subprocess.call(zmmboxproc.split(' '))
            print '\n'





    def main(self):
        #print 'Extractions des utilisateurs'
        self.extract_users()
        self.create_users()
        zmprovproc = [self.zmprov,'-f','user_creation']
        print zmprovproc
        zmprovproc = subprocess.call(zmprovproc)
        print '\n'
        #print 'Extraction des e-mail de chaque utilisateur'
        for user in self.users:
            MailDir.extract_folders(user, self.path)
        self.import_mails()


runner = Main("/mnt/elus-ville-acigne.fr", "elu-ville-acigne.fr")
runner.main()