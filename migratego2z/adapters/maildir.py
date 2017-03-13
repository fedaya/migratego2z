# -*- coding: utf-8 -*-
from imapclient import imap_utf7
from typing import List
from migratego2z.go_db import EmAccount
import re
import os


class MailDir:
    """
    This class represents Group-Office's maildirs
    """

    def __init__(self, name: str, full_name: str, parent: 'MailDir' = None):
        chain = name.split('.')
        folder = chain[len(chain) - 1]
        folder = folder.encode('utf-8')
        # print(folder + ' is, when decoded '+ imap_utf7.decode(folder))
        self.name = imap_utf7.decode(folder)
        self.original_name = full_name
        self._children = []
        self._parent = parent

    def add_child(self, child: 'MailDir'):
        """
        Adds a child to the maildir
        :param child: a child maildir
        :return: nothing
        """
        if child is not None:
            self._children.append(child)

    def get_child(self, name: str) -> 'MailDir':
        """
        Return the child with the name child
        :param name: the child to look for
        :return: the child or None
        """
        for child in self._children:
            if child.name == name or child.name == imap_utf7.decode(name) or child.original_name == name:
                return child
        return None

    def get_children(self) -> 'MailDir':
        """

        :return: Return the children in case you'd need it
        """
        return self._children

    def get_path(self) -> str:
        """
        Returns the expected path of the maildir in Zimbra
        :return: the expected path of the maildir
        """
        if self._parent is None:
            return '/' + self.name
        else:
            return self._parent.get_path() + '/' + self.name

    def _prep_path(self, path: str) -> str:
        """
        Prepare the path in parameters, stripping unwanted /./ and /., double escaping single quotes for compatibility
        :param path: the path to treat
        :return: treated path
        """
        retpath = path
        return retpath.replace('/./', '/').replace('/.', '/').replace('\'', '\\\'').replace('//', '/')

    def _get_creation_string(self) -> str:
        """
        Returns the string used by Zimbra to create the folder
        :param prefix: If needed, a prefix for the target folders
        :return: zimbra's folder creation string
        """
        return 'createFolder \'' + self._prep_path(self.get_path()) + '\''

    def _get_messages_string(self, base_folder: str) ->str:
        """
        Returns the string used by Zimbra add messages from a maildir
        :return: zimbra's add message string
        """
        return_string = 'addMessage --noValidation \'' + self._prep_path(self.get_path()) + '\' \'' + base_folder + \
                        '/' + self._prep_path(self.original_name) + '/cur\'\n'
        return_string += 'addMessage --noValidation \'' + self._prep_path(self.get_path()) + '\' \'' + base_folder + \
                         '/' + self._prep_path(self.original_name) + '/new\'\n'
        return return_string

    def get_tree_creation(self, special_folders: List[str]) -> str:
        """
        Recursively returns Zimbra's script to create all the folders.
        Call this function only from root folder
        :param special_folders: A list of special folders you won't create
        :param prefix: If needed, a prefix for the target folders
        :return: zimbra's script
        """
        return_string = ''
        if self._parent is not None:
            return_string += self._get_creation_string() + '\n'
        for child in self._children:
            if child is not None:
                if child.name not in special_folders:
                    return_string += child.get_tree_creation(special_folders)
        return return_string

    def get_tree_messages(self, email_account: EmAccount, base_folder: str) -> str:
        root_folder = get_email_base_account(email_account, base_folder)
        return_string = self._get_messages_string(root_folder)
        for child in self._children:
            if child is not None:
                return_string += child.get_tree_messages(email_account, base_folder)
        return return_string


def get_email_base_account(email_account: EmAccount, base_folder: str) -> str:
    [folder, domain] = email_account.username.split('@')
    return base_folder + '/' + domain + '/' + folder


def extract_folders(email_account: EmAccount, base_folder: str) -> MailDir:
    """
    Extracts the mail folders structure for an e-mail account
    :param email_account: the e-mail account for which we want the mail folders structures
    :param base_folder: Group-Office root vmail folder
    :return: a populated MailDir tree
    """
    root_folder = get_email_base_account(email_account, base_folder)
    # first, let's extract the list of folders in the expected maildir
    dir_list = os.listdir(root_folder)
    base_mail_dir = None
    # here we check if we are indeed in a maildir and if so create the base mailDir in memory
    for entry in dir_list:
        if os.path.isdir(os.path.join(root_folder, entry)) and entry == 'cur':
            base_mail_dir = MailDir('.','.')
            break
    if base_mail_dir is None:
        return Exception('Folder specified is not a mailDir')
    # then, we extract every folder name into a tree of mailDir
    for entry in dir_list:
        # checking if it is a possible mailDir:
        if os.path.isdir(os.path.join(root_folder, entry)) and \
                        entry not in ['cur', 'new', 'sieve', 'tmp']:
            dir_name = entry
            full_name = dir_name
            # here we split between the first folder name and the subsequents
            matches = re.match('\.([^.]+)(\..*)?', dir_name)
            cur_mail_dir = base_mail_dir
            while matches is not None:
                # We'll do a little loop, creating the maildirs, until we have the last one
                if matches.group(1) != 'INBOX':
                    # Looking if the folder already exist in memory
                    new_mail_dir = cur_mail_dir.get_child(matches.group(1))
                    if new_mail_dir is None:
                        new_mail_dir = MailDir(matches.group(1), entry, cur_mail_dir)
                        cur_mail_dir.add_child(new_mail_dir)
                    cur_mail_dir = new_mail_dir
                dir_name = matches.group(2)
                if dir_name is not None:
                    matches = re.match('\.([^.]+)(\..*)?', dir_name)
                else:
                    matches = None
    return base_mail_dir
