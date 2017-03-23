# -*- coding: utf-8 -*-

from migratego2z.go_db import AbAddressbook, AbContact, AbCompany
import vobject
import sqlalchemy
import urllib
import pprint
from migratego2z.config import ZimbraAdminConfig


def generate_vcf(contacts: sqlalchemy.engine.ResultProxy, base_name: str, contactbookname: str,
                 username: str, zimbra: ZimbraAdminConfig) -> (str, str):
    """
    Generates the Addressbook from AbContact LeftJoin AbCompany passed in argument into a vcf file.

    :param contacts: The AbContact extracted from database
    :param base_name: The base of output vcf filename, including its full path. Truncated on opening
    :param contactbookname: The contact folder name
    :param username: The username concerned with this extraction (for zimbra's string)
    :return: Zimbra's and sh insertion string
    """

    filename = base_name + '.' + contactbookname + '.' + username + '.vcf'
    file = open(filename, 'w', encoding='utf-8')
    file_content = ""
    for contact in contacts:
        card = vobject.vCard()
        card.add('fn')
        card.fn.value = contact['first_name'] + ' ' + \
                        (contact['middle_name'] + ' ' if contact['middle_name'] != '' else '') + \
                        contact['last_name']
        card.add('n')
        card.n.value = vobject.vcard.Name(family=contact['last_name'], given=contact['first_name'])
        if contact['email'] != "":
            card.add('email')
            card.email.value = contact['email']
            card.email.type_param = 'PREF,INTERNET'
            if contact['email2'] != "":
                card.add('email')
                card.contents['email'][1].value = contact['email2']
                card.contents['email'][1].type_param = 'INTERNET'
                if contact.email3 != "":
                    card.add('email')
                    card.contents['email'][2].value = contact['email3']
                    card.contents['email'][2].type_param = 'INTERNET'
        if contact['company_id'] != 0:
            card.add('org')
            card.org.value = [contact['name']]
        if contact['home_phone'] != "":
            card.add('tel')
            card.tel.value = contact['home_phone']
            card.tel.type_param = 'HOME;VOICE'
        if contact['fax'] != "":
            card.add('tel')
            card.contents['tel'][len(card.contents['tel']) - 1].value = contact['fax']
            card.contents['tel'][len(card.contents['tel']) - 1].type_param = 'HOME;FAX'
        if contact['work_phone'] != "":
            card.add('tel')
            card.contents['tel'][len(card.contents['tel']) - 1].value = contact['work_phone']
            card.contents['tel'][len(card.contents['tel']) - 1].type_param = 'WORK;VOICE'
        if contact['work_fax'] != "":
            card.add('tel')
            card.contents['tel'][len(card.contents['tel']) - 1].value = contact['work_fax']
            card.contents['tel'][len(card.contents['tel']) - 1].type_param = 'WORK;FAX'
        if contact['cellular'] != "":
            card.add('tel')
            card.contents['tel'][len(card.contents['tel']) - 1].value = contact['cellular']
            card.contents['tel'][len(card.contents['tel']) - 1].type_param = 'CELL'
        if contact['cellular2'] != "":
            card.add('tel')
            card.contents['tel'][len(card.contents['tel']) - 1].value = contact['cellular2']
            card.contents['tel'][len(card.contents['tel']) - 1].type_param = 'CELL'
        if contact['uuid'] != "":
            card.add('uid')
            card.uid.value = contact['uuid']
        if contact['homepage'] is not None:
            card.add('url')
            card.url.value = contact['homepage']
        if contact['address'] != "":
            card.add('adr')
            adr = vobject.vcard.Address(
                street=((contact['address_no'] + ", ") if contact['address_no'] != '' else '') + contact['address'],
                city=contact['city'],
                country=contact['country'],
                code=contact['zip'])
            card.adr.value = adr
        if contact['comment'] != "" and contact['comment'] is not None:
            card.add('note')
            card.note.value = contact['comment']
        file_content += card.serialize()
    # file.write(file_content.encode('utf-8'))\
    file.write(file_content)
    file.close()

    return_zimbra = "selectMailbox -A " + username + "\n"
    return_zimbra += "createFolder --view contact \"/" + contactbookname + "\"\n"
    return_script = "curl -k -v -u " + zimbra.login + ":" + zimbra.password + " " + zimbra.url + username + \
                         '/' + urllib.parse.quote(contactbookname) + ' --upload-file \"' + \
                         filename + '\"\n'
    return return_zimbra, return_script
