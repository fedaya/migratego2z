# -*- coding: utf-8 -*-
from migratego2z.go_db import GoUser, EmAccount
from typing import List
from typing import Dict
import string
import random
import re
import os
import sqlalchemy


def pw_gen(size=8, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def create_users(users: List[GoUser], domain: str, connection: sqlalchemy.engine.Connection, base_folder: str) \
        -> (str, Dict[int, List[str]], List[str]):
    """
    Return Zimbra's creation script for the users specified in parameter
    Also creates a file with the same information if a filename is specified

    :param users: List of users you want to create
    :param domain: E-mail domain for target user
    :param connection: The db connection
    :param filename: if specified, this file is written with Zimbra's creation script
    :return: Zimbra's creation script as a string
    """

    return_string = ''
    supp_email = {}
    supp_email_addresses = []
    for user in users:
        base_email = user.username + '@' + domain
        user_creation_string = 'createAccount ' + base_email + ' \'{CRYPT}' + user.password + \
                               '\' givenName \'' + user.first_name + '\' sn \'' + user.last_name + '\'\n'
        return_string += user_creation_string
        email_accounts = get_user_email_accounts(user, connection, domain)
        for email in email_accounts:
            if email.username != base_email:
                supp_email_string = ''
                if email.username not in supp_email_addresses:
                    supp_email_addresses.append(email.username)
                    supp_email_string = 'createAccount ' + email.username + ' \'' + pw_gen(64) + '\'\n'
                if email.user_id in supp_email:
                    supp_email[email.user_id].append(email.username)
                else:
                    supp_email[email.user_id] = [email.username]
                supp_email_string += 'grantRight account ' + email.username + ' usr ' + base_email + ' sendAs\n'
                return_string += supp_email_string
    matches = re.findall('(createAccount [^ ]+\@[^ ]+)[^\n]*\n', return_string)
    seen = []
    duplicates = []
    for x in matches:
        if x in seen:
            duplicates.append(x)
        else:
            seen.append(x)
    for duplicate in duplicates:
        matches = re.findall('('+duplicate+'[^\n]*\n)', return_string)
        for match in matches:
            if r'{CRYPT}' not in match:
                return_string = re.sub(match, '', return_string)
    filename = os.path.join(base_folder, 'users_creation.zmp')
    user_creation_file = open(filename, 'w')
    # user_creation_file.write(return_string.encode('utf-8'))
    user_creation_file.write(return_string)
    user_creation_file.close()
    return filename, return_string, supp_email, supp_email_addresses


def get_user_email_accounts(user: GoUser, connection: sqlalchemy.engine.Connection, domain:str) -> List[EmAccount]:
    """
    Return a list of the user's e-mail accounts for pratical purposes, as a user can have multiple e-mail accounts
    :param user: the user you want to obtain the list of e-mail accounts of
    :param connection: the db connection
    :return: a List of e-mail accounts
    """
    s = sqlalchemy.select([EmAccount]).where(EmAccount.user_id == user.id).where(EmAccount.username.like('%'+domain))
    result = connection.execute(s)
    return_list = []
    for row in result:
        return_list.append(row)
    return return_list
