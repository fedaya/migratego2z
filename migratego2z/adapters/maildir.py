# -*- coding: utf-8 -*-
from imapclient import imap_utf7
from typing import List
from typing import Dict

from migratego2z.go_db import EmAccount
import re
import os



class MailDir:
    """
    This class represents Group-Office's maildirs
    """

    def __init__(self, name: str, full_name: str, parent: 'MailDir' = None):
        if name != ".":
            chain = name.split('.')
            folder = chain[len(chain) - 1]
            folder = folder.encode('utf-8')
            # print(folder + ' is, when decoded '+ imap_utf7.decode(folder))
            self.name = imap_utf7.decode(folder)
        else:
            self.name = name
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
            if child.name == name or child.name == imap_utf7.decode(name) or name in child.original_name:
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
            return '/Inbox'
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
        path = self._prep_path(self.get_path())
        if path not in ['/', '/Junk', '/Sent', '/Drafts', '/Trash', '/Briefcase', '/Calendar', '/Chats',
                           '/Contacts', '/Email Contacts', '/Inbox', '/Tasks']:
            return 'createFolder --view message \"' + path + '\"\n'
        return ''

    def _get_messages_string(self, base_folder: str, is_special: bool) ->str:
        """
        Returns the string used by Zimbra add messages from a maildir
        :return: zimbra's add message string
        """
        # add_message = 'addMessage --noValidation ' + \
        #               ('/' + self.rand_name if not is_special else
        #                self._prep_path(self.get_path()).replace('Spam', 'Junk')) + ' \"' + \
        #               base_folder + '/' + self._prep_path(self.original_name)
        add_message = 'addMessage --noValidation \"' + self._prep_path(self.get_path()).replace('Spam', 'Junk') + \
                      '\" \"' + base_folder + '/' + self._prep_path(self.original_name)
        if is_special and self.name != '.':
            add_message = re.sub(r'/Inbox/', r'/', add_message)
        return_string = add_message + '/cur\"\n'
        return_string += add_message + '/new\"\n'
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
            return_string += self._get_creation_string()
        for child in self._children:
            if child is not None:
                if child.name not in special_folders:
                    return_string += child.get_tree_creation(special_folders)
        return return_string

    def get_tree_messages(self, email_account: EmAccount, base_folder: str, special_folders: List[str]) -> str:
        root_folder = get_email_base_account(email_account, base_folder)
        return_string = self._get_messages_string(root_folder, self.name in special_folders)
        for child in self._children:
            if child is not None:
                return_string += child.get_tree_messages(email_account, base_folder, special_folders)
        return return_string

    def to_string(self, sub = 0):
        if sub == 0:
            print('=====new maildir tree=====')
        print('*'*sub + self.original_name)
        for child in self._children:
            child.to_string(sub+1)


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
    debug = 0
    # here we check if we are indeed in a maildir and if so create the base mailDir in memory
    for entry in dir_list:
        if os.path.isdir(os.path.join(root_folder, entry)) and entry == 'cur':
            base_mail_dir = MailDir('.', '.')
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
            first_part = ''
            # here we split between the first folder name and the subsequents
            matches = re.match('\.([^\.]+)(\..+)?', dir_name)
            cur_mail_dir = base_mail_dir
            while matches is not None:
                # We'll do a little loop, creating the maildirs, until we have the last one
                if matches.group(1) != 'INBOX':
                    first_part += '.' + matches.group(1)
                    # Looking if the folder already exist in memory
                    new_mail_dir = cur_mail_dir.get_child(matches.group(1))
                    if new_mail_dir is None:
                        new_mail_dir = MailDir(matches.group(1), first_part, cur_mail_dir)
                        cur_mail_dir.add_child(new_mail_dir)
                    cur_mail_dir = new_mail_dir
                dir_name = matches.group(2)
                if dir_name is not None:
                    matches = re.match('\.([^\.]+)(\..+)?', dir_name)
                else:
                    matches = None
    # base_mail_dir.to_string()
    return base_mail_dir


def import_mails(email_accounts: List[EmAccount], supp_email: Dict[int, List[str]], supp_email_addresses: List[str],
                 root_path: str, base_folder: str) -> (str, str):
    import_str = ''
    import_str2 = ''
    for email in email_accounts:
        tmp_str = ''
        if email.username not in supp_email_addresses and email.user_id in supp_email:
            user = email.username
            users_sup_email = supp_email[email.user_id]
            for sharer in users_sup_email:
                # print('sharing ' + sharer + ' with ' + user)
                import_str += 'selectMailbox -A ' + sharer + '\n'
                import_str += 'modifyFolderGrant / account ' + user + ' rwixd\n'
                import_str += 'selectMailbox -A ' + user + '\n'
                import_str += 'createMountpoint /' + sharer + ' ' + sharer + ' /\n'
        else:
            if re.search('selectMailbox ' + email.username + '\n(modifyFolderGrant){0}', import_str) is None:
                import_str += 'selectMailbox ' + email.username + '\n'
                import_str += tmp_str
                user_maildir = extract_folders(email, root_path)
                special_folders = [email.sent, email.drafts, email.trash, email.spam, '.']
                import_str += user_maildir.get_tree_creation(special_folders)
                import_str2 += 'selectMailbox ' + email.username + '\n'
                import_str2 += user_maildir.get_tree_messages(email, root_path, special_folders)
    filenames = [os.path.join(base_folder, 'mail_copy.zmm'), os.path.join(base_folder, 'mail_copy_2.zmm')]
    user_import = open(filenames[0], 'w', encoding='utf-8')
    # user_import.write(import_str.encode('utf-8'))
    user_import.write(import_str)
    user_import.close()
    user_import = open(filenames[1], 'w', encoding='utf-8')
    user_import.write(import_str2)
    user_import.close()
    return filenames, import_str
