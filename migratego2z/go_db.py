# coding: utf-8
from sqlalchemy import BigInteger, Column, Date, Enum, Float, Index, Integer, LargeBinary, Numeric, SmallInteger, String, Table, Text, Time, VARBINARY, text
from sqlalchemy.dialects.mysql.types import LONGBLOB, MEDIUMBLOB
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class AbAddressbook(Base):
    __tablename__ = 'ab_addressbooks'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(100))
    acl_id = Column(Integer, nullable=False, server_default=text("'0'"))
    default_salutation = Column(String(255), nullable=False)
    files_folder_id = Column(Integer, nullable=False, server_default=text("'0'"))
    users = Column(Integer, nullable=False, server_default=text("'0'"))


class AbAddresslistCompany(Base):
    __tablename__ = 'ab_addresslist_companies'

    addresslist_id = Column(Integer, primary_key=True, nullable=False)
    company_id = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))


class AbAddresslistContact(Base):
    __tablename__ = 'ab_addresslist_contacts'

    addresslist_id = Column(Integer, primary_key=True, nullable=False)
    contact_id = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))


class AbAddresslist(Base):
    __tablename__ = 'ab_addresslists'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, server_default=text("'0'"))
    acl_id = Column(Integer, nullable=False, server_default=text("'0'"))
    name = Column(String(255))
    default_salutation = Column(String(50))


class AbCompany(Base):
    __tablename__ = 'ab_companies'

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, index=True)
    user_id = Column(Integer, nullable=False, server_default=text("'0'"))
    addressbook_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(100), server_default=text("''"))
    name2 = Column(String(100), server_default=text("''"))
    address = Column(String(100), server_default=text("''"))
    address_no = Column(String(100), server_default=text("''"))
    zip = Column(String(10), server_default=text("''"))
    city = Column(String(50), server_default=text("''"))
    state = Column(String(50), server_default=text("''"))
    country = Column(String(50), server_default=text("''"))
    post_address = Column(String(100), server_default=text("''"))
    post_address_no = Column(String(100), nullable=False, server_default=text("''"))
    post_city = Column(String(50), server_default=text("''"))
    post_state = Column(String(50), server_default=text("''"))
    post_country = Column(String(50), server_default=text("''"))
    post_zip = Column(String(10), server_default=text("''"))
    phone = Column(String(30), server_default=text("''"))
    fax = Column(String(30), server_default=text("''"))
    email = Column(String(75), index=True, server_default=text("''"))
    homepage = Column(String(100), server_default=text("''"))
    comment = Column(Text)
    bank_no = Column(String(50), server_default=text("''"))
    bank_bic = Column(String(11), nullable=False, server_default=text("''"))
    vat_no = Column(String(30), server_default=text("''"))
    invoice_email = Column(String(75), server_default=text("''"))
    ctime = Column(Integer, nullable=False, server_default=text("'0'"))
    mtime = Column(Integer, nullable=False, server_default=text("'0'"))
    email_allowed = Column(Integer, nullable=False, server_default=text("'1'"))
    files_folder_id = Column(Integer, nullable=False, server_default=text("'0'"))
    crn = Column(String(50), server_default=text("''"))
    iban = Column(String(100), server_default=text("''"))
    muser_id = Column(Integer, nullable=False, server_default=text("'0'"))
    photo = Column(String(255), nullable=False, server_default=text("''"))
    color = Column(String(6), nullable=False, server_default=text("'000000'"))


class AbContact(Base):
    __tablename__ = 'ab_contacts'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(255, 'ascii_bin'), nullable=False, index=True, server_default=text("''"))
    user_id = Column(Integer, nullable=False, server_default=text("'0'"))
    addressbook_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    first_name = Column(String(50), nullable=False, server_default=text("''"))
    middle_name = Column(String(50), nullable=False, server_default=text("''"))
    last_name = Column(String(50), nullable=False, index=True, server_default=text("''"))
    initials = Column(String(10), nullable=False, server_default=text("''"))
    title = Column(String(50), nullable=False, server_default=text("''"))
    suffix = Column(String(50), nullable=False, server_default=text("''"))
    sex = Column(Enum('M', 'F'), nullable=False, server_default=text("'M'"))
    birthday = Column(Date)
    email = Column(String(100), nullable=False, index=True, server_default=text("''"))
    email2 = Column(String(100), nullable=False, index=True, server_default=text("''"))
    email3 = Column(String(100), nullable=False, index=True, server_default=text("''"))
    company_id = Column(Integer, nullable=False, server_default=text("'0'"))
    department = Column(String(100), nullable=False, server_default=text("''"))
    function = Column(String(50), nullable=False, server_default=text("''"))
    home_phone = Column(String(30), nullable=False, server_default=text("''"))
    work_phone = Column(String(30), nullable=False, server_default=text("''"))
    fax = Column(String(30), nullable=False, server_default=text("''"))
    work_fax = Column(String(30), nullable=False, server_default=text("''"))
    cellular = Column(String(30), nullable=False, server_default=text("''"))
    homepage = Column(String(255))
    country = Column(String(50), nullable=False, server_default=text("''"))
    state = Column(String(50), nullable=False, server_default=text("''"))
    city = Column(String(50), nullable=False, server_default=text("''"))
    zip = Column(String(10), nullable=False, server_default=text("''"))
    address = Column(String(100), nullable=False, server_default=text("''"))
    address_no = Column(String(100), nullable=False, server_default=text("''"))
    comment = Column(Text)
    ctime = Column(Integer, nullable=False, server_default=text("'0'"))
    mtime = Column(Integer, nullable=False, server_default=text("'0'"))
    salutation = Column(String(100), nullable=False, server_default=text("''"))
    email_allowed = Column(Integer, nullable=False, server_default=text("'1'"))
    files_folder_id = Column(Integer, nullable=False, server_default=text("'0'"))
    go_user_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    cellular2 = Column(String(30), nullable=False, server_default=text("''"))
    muser_id = Column(Integer, nullable=False, server_default=text("'0'"))
    photo = Column(String(255), nullable=False, server_default=text("''"))
    action_date = Column(Integer, nullable=False, server_default=text("'0'"))
    url_linkedin = Column(String(100))
    url_facebook = Column(String(100))
    url_twitter = Column(String(100))
    skype_name = Column(String(100))
    color = Column(String(6), nullable=False, server_default=text("'000000'"))


class AbContactsVcardProp(Base):
    __tablename__ = 'ab_contacts_vcard_props'

    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    name = Column(String(255), nullable=False, server_default=text("''"))
    parameters = Column(String(1023), nullable=False, server_default=text("''"))
    value = Column(String(1023), nullable=False, server_default=text("''"))


class CalCalendar(Base):
    __tablename__ = 'cal_calendars'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, nullable=False, index=True, server_default=text("'1'"))
    user_id = Column(Integer, nullable=False, server_default=text("'0'"))
    acl_id = Column(Integer, nullable=False, server_default=text("'0'"))
    name = Column(String(100))
    start_hour = Column(Integer, nullable=False, server_default=text("'0'"))
    end_hour = Column(Integer, nullable=False, server_default=text("'0'"))
    background = Column(String(6))
    time_interval = Column(Integer, nullable=False, server_default=text("'1800'"))
    public = Column(Integer, nullable=False, server_default=text("'0'"))
    shared_acl = Column(Integer, nullable=False, server_default=text("'0'"))
    show_bdays = Column(Integer, nullable=False, server_default=text("'0'"))
    show_completed_tasks = Column(Integer, nullable=False, server_default=text("'1'"))
    comment = Column(String(255), nullable=False, server_default=text("''"))
    project_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    tasklist_id = Column(Integer, nullable=False, server_default=text("'0'"))
    files_folder_id = Column(Integer, nullable=False, server_default=text("'0'"))
    show_holidays = Column(Integer, nullable=False, server_default=text("'1'"))
    enable_ics_import = Column(Integer, nullable=False, server_default=text("'0'"))
    ics_import_url = Column(String(512), nullable=False, server_default=text("''"))
    tooltip = Column(String(127), nullable=False, server_default=text("''"))
    version = Column(Integer, nullable=False, server_default=text("'1'"))


class CalCategory(Base):
    __tablename__ = 'cal_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    color = Column(String(6), nullable=False, server_default=text("'EBF1E2'"))
    calendar_id = Column(Integer, nullable=False, index=True)
    acl_id = Column(Integer, nullable=False, server_default=text("'0'"))
    user_id = Column(Integer, nullable=False)


class CalEvent(Base):
    __tablename__ = 'cal_events'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(255, 'ascii_bin'), nullable=False, index=True, server_default=text("''"))
    calendar_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, server_default=text("'0'"))
    start_time = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    end_time = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    all_day_event = Column(Integer, nullable=False, server_default=text("'0'"))
    name = Column(String(150), nullable=False)
    description = Column(Text)
    location = Column(String(100), nullable=False, server_default=text("''"))
    repeat_end_time = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    reminder = Column(Integer, nullable=False, server_default=text("'0'"))
    ctime = Column(Integer, nullable=False, server_default=text("'0'"))
    mtime = Column(Integer, nullable=False, server_default=text("'0'"))
    busy = Column(Integer, nullable=False, index=True, server_default=text("'1'"))
    status = Column(String(20), nullable=False, server_default=text("'NEEDS-ACTION'"))
    resource_event_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    private = Column(Integer, nullable=False, server_default=text("'0'"))
    rrule = Column(String(100), nullable=False, index=True, server_default=text("''"))
    background = Column(String(6), nullable=False, server_default=text("'ebf1e2'"))
    files_folder_id = Column(Integer, nullable=False, server_default=text("'0'"))
    read_only = Column(Integer, nullable=False, server_default=text("'0'"))
    category_id = Column(Integer, index=True)
    exception_for_event_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    recurrence_id = Column(String(20), nullable=False, index=True, server_default=text("''"))
    is_organizer = Column(Integer, nullable=False, server_default=text("'1'"))
    muser_id = Column(Integer, nullable=False, server_default=text("'0'"))


class CalParticipant(Base):
    __tablename__ = 'cal_participants'
    __table_args__ = (
        Index('event_id_2', 'event_id', 'email', unique=True),
        Index('event_id', 'event_id', 'user_id')
    )

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False)
    name = Column(String(100))
    email = Column(String(100))
    user_id = Column(Integer, nullable=False, server_default=text("'0'"))
    contact_id = Column(Integer, nullable=False, server_default=text("'0'"))
    status = Column(String(50), nullable=False, server_default=text("'NEEDS-ACTION'"))
    last_modified = Column(String(20), nullable=False, server_default=text("''"))
    is_organizer = Column(Integer, nullable=False, server_default=text("'0'"))
    role = Column(String(100), nullable=False, server_default=text("''"))


class GoUser(Base):
    __tablename__ = 'go_users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    digest = Column(String(255), nullable=False, server_default=text("''"))
    enabled = Column(Integer, nullable=False, server_default=text("'1'"))
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=False, server_default=text("''"))
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    acl_id = Column(Integer, nullable=False, server_default=text("'0'"))
    date_format = Column(String(20), nullable=False, server_default=text("'dmY'"))
    date_separator = Column(String(1), nullable=False, server_default=text("'-'"))
    time_format = Column(String(10), nullable=False, server_default=text("'G:i'"))
    thousands_separator = Column(String(1), nullable=False, server_default=text("'.'"))
    decimal_separator = Column(String(1), nullable=False, server_default=text("','"))
    currency = Column(String(3), nullable=False, server_default=text("''"))
    logins = Column(Integer, nullable=False, server_default=text("'0'"))
    lastlogin = Column(Integer, nullable=False, server_default=text("'0'"))
    ctime = Column(Integer, nullable=False, server_default=text("'0'"))
    max_rows_list = Column(Integer, nullable=False, server_default=text("'20'"))
    timezone = Column(String(50), nullable=False, server_default=text("'Europe/Amsterdam'"))
    start_module = Column(String(50), nullable=False, server_default=text("'summary'"))
    language = Column(String(20), nullable=False, server_default=text("'en'"))
    theme = Column(String(20), nullable=False, server_default=text("'Default'"))
    first_weekday = Column(Integer, nullable=False, server_default=text("'0'"))
    sort_name = Column(String(20), nullable=False, server_default=text("'first_name'"))
    mtime = Column(Integer, nullable=False, server_default=text("'0'"))
    mute_sound = Column(Integer, nullable=False, server_default=text("'0'"))
    mute_reminder_sound = Column(Integer, nullable=False, server_default=text("'0'"))
    mute_new_mail_sound = Column(Integer, nullable=False, server_default=text("'0'"))
    show_smilies = Column(Integer, nullable=False, server_default=text("'1'"))
    auto_punctuation = Column(Integer, nullable=False, server_default=text("'0'"))
    list_separator = Column(String(3), nullable=False, server_default=text("';'"))
    text_separator = Column(String(3), nullable=False, server_default=text("'\"'"))
    files_folder_id = Column(Integer, nullable=False, server_default=text("'0'"))
    disk_usage = Column(BigInteger, nullable=False, server_default=text("'0'"))
    disk_quota = Column(BigInteger)
    mail_reminders = Column(Integer, nullable=False, server_default=text("'0'"))
    popup_reminders = Column(Integer, nullable=False, server_default=text("'0'"))
    password_type = Column(String(20), nullable=False, server_default=text("'crypt'"))
    muser_id = Column(Integer, nullable=False, server_default=text("'0'"))
    holidayset = Column(String(10))
    sort_email_addresses_by_time = Column(Integer, nullable=False, server_default=text("'0'"))
    no_reminders = Column(Integer, nullable=False, server_default=text("'0'"))


class GoAcl(Base):
    __tablename__ = 'go_acl'
    __table_args__ = (
        Index('acl_id', 'acl_id', 'user_id'),
        Index('acl_id_2', 'acl_id', 'group_id')
    )

    acl_id = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))
    user_id = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))
    group_id = Column(Integer, primary_key=True, nullable=False, server_default=text("'0'"))

    level = Column(Integer, nullable=False, server_default=text("'10'"))


class EmAccount(Base):
    __tablename__ = 'em_accounts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    acl_id = Column(Integer, nullable=False, index=True, server_default=text("'0'"))
    type = Column(String(4, u'utf8mb4_unicode_ci'))
    host = Column(String(100, u'utf8mb4_unicode_ci'))
    port = Column(Integer, nullable=False, server_default=text("'0'"))
    deprecated_use_ssl = Column(Integer, nullable=False, server_default=text("'0'"))
    novalidate_cert = Column(Integer, nullable=False, server_default=text("'0'"))
    username = Column(String(50, u'utf8mb4_unicode_ci'))
    password = Column(String(255, u'utf8mb4_unicode_ci'))
    imap_encryption = Column(String(3, u'utf8mb4_unicode_ci'), nullable=False)
    imap_allow_self_signed = Column(Integer, nullable=False, server_default=text("'1'"))
    mbroot = Column(String(30, u'utf8mb4_unicode_ci'), nullable=False, server_default=text("''"))
    sent = Column(String(100, u'utf8mb4_unicode_ci'), server_default=text("'Sent'"))
    drafts = Column(String(100, u'utf8mb4_unicode_ci'), server_default=text("'Drafts'"))
    trash = Column(String(100, u'utf8mb4_unicode_ci'), nullable=False, server_default=text("'Trash'"))
    spam = Column(String(100, u'utf8mb4_unicode_ci'), nullable=False, server_default=text("'Spam'"))
    smtp_host = Column(String(100, u'utf8mb4_unicode_ci'))
    smtp_port = Column(Integer, nullable=False)
    smtp_encryption = Column(String(3, u'utf8mb4_unicode_ci'), nullable=False)
    smtp_allow_self_signed = Column(Integer, nullable=False, server_default=text("'0'"))
    smtp_username = Column(String(50, u'utf8mb4_unicode_ci'))
    smtp_password = Column(String(255, u'utf8mb4_unicode_ci'), nullable=False, server_default=text("''"))
    password_encrypted = Column(Integer, nullable=False, server_default=text("'0'"))
    ignore_sent_folder = Column(Integer, nullable=False, server_default=text("'0'"))
    sieve_port = Column(Integer, nullable=False)
    sieve_usetls = Column(Integer, nullable=False, server_default=text("'1'"))
    check_mailboxes = Column(String(collation=u'utf8mb4_unicode_ci'))
    do_not_mark_as_read = Column(Integer, nullable=False, server_default=text("'0'"))
    signature_below_reply = Column(Integer, nullable=False, server_default=text("'0'"))
    full_reply_headers = Column(Integer, nullable=False, server_default=text("'0'"))


class PaAlias(Base):
    __tablename__ = 'pa_aliases'

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, nullable=False, index=True)
    address = Column(String(190, u'utf8mb4_unicode_ci'), index=True)
    goto = Column(String(collation=u'utf8mb4_unicode_ci'))
    ctime = Column(Integer, nullable=False, server_default=text("'0'"))
    mtime = Column(Integer, nullable=False, server_default=text("'0'"))
    active = Column(Enum(u'0', u'1'), nullable=False, server_default=text("'1'"))
