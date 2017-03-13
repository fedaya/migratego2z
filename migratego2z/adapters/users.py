# -*- coding: utf-8 -*-
from migratego2z.go_db import GoUser, EmAccount
from typing import List
from typing import Dict
from migratego2z.config import Config
import string
import random
import re
import sqlalchemy


def pw_gen(size=8, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def create_users(users: List[GoUser], domain: str, config: Config, filename: str = None) \
        -> (str, Dict[int, List[str]], List[str]):
    """
    Return Zimbra's creation script for the users specified in parameter
    Also creates a file with the same information if a filename is specified

    :param users: List of users you want to create
    :param domain: E-mail domain for target user
    :param config: The config object
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
        email_accounts = get_user_email_accounts(user, config)
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
    print(return_string)
    if filename is not None:
        user_creation_file = open(filename, 'wb')
        user_creation_file.write(return_string.encode('utf-8'))
        user_creation_file.close()
    return return_string, supp_email, supp_email_addresses


def get_user_email_accounts(user: GoUser, config: Config) -> List[EmAccount]:
    """
    Return a list of the user's e-mail accounts for pratical purposes, as a user can have multiple e-mail accounts
    :param user: the user you want to obtain the list of e-mail accounts of
    :param config: As there is a db connection, we pass the config class
    :return: a List of e-mail accounts
    """
    engine = sqlalchemy.create_engine(
        'mysql+mysqlconnector://' + config.db.user + ':' + config.db.password +
        '@' + config.db.host + '/' + config.db.database)
    conn = engine.connect()
    s = sqlalchemy.select([EmAccount]).where(EmAccount.user_id == user.id).where(EmAccount.username.like('%'+config.domain))
    result = conn.execute(s)
    return_list = []
    for row in result:
        return_list.append(row)
    return return_list
