# -*- coding: utf-8 -*-

from migratego2z.go_db import CalEvent, CalCalendar, EmAccount
from typing import List
import sqlalchemy
import vobject
from migratego2z.config import ZimbraAdminConfig
from time import time
from datetime import datetime

import urllib


class Calendar:
    def __init__(self, calendar: CalCalendar):
        self._events = []
        self._calendar = calendar
        # Zimbra doesn't allow ics file with more than 500 events. In that case cut in portions (of 499 just to be safe)
        self.limit = False

    def add_event(self, event: CalEvent):
        self._events.append(event)

    def get_events(self) -> List[CalEvent]:
        return self._events

    def get_events_count(self):
        return len(self._events)

    def get_event(self, name: str) -> CalEvent:
        for event in self._events:
            if event.name == name:
                return event

    def get_calendar(self) -> CalCalendar:
        return self._calendar

    def get_ical(self, portion: int = -1):
        ics = vobject.iCalendar()
        events = self._events
        if portion != -1:
            # here comes the 499 in lower and upper bounds
            lb = portion * 499
            ub = (1 + portion) * 499 - 1
            events = self._events[lb:ub]

        for event in events:
            ics.add('vevent')
            i_event = ics.contents['vevent'][len(ics.contents['vevent']) - 1]
            i_event.add('summary').value = event.name
            start_time = datetime.fromtimestamp(event.start_time, None)
            end_time = datetime.fromtimestamp(event.end_time, None)
            i_event.add('dtstart').value = start_time
            i_event.add('dtend').value = end_time
            if event.status in ['TENTATIVE', 'CONFIRMED', 'CANCELLED']:
                i_event.add('status').value = event.status
            else:
                i_event.add('status').value = 'TENTATIVE'
            if event.description != '' and event.description is not None:
                i_event.add('description').value = event.description
            if event.location != '' and event.location is not None:
                i_event.add('location').value = event.location
            i_event.add('transp').value = 'OPAQUE' if event.busy == 1 else 'TRANSPARENT'
            if event.rrule != '' and event.rrule is not None:
                i_event.add('rrule').value = event.rrule
            i_event.add('class').value = 'PUBLIC' if event.private == 0 else 'PRIVATE'
            i_event.add('uid').value = event.uuid
            if event.mtime != 0:
                i_event.add('dtstamp').value = datetime.fromtimestamp(event.mtime, tz=None)
            elif event.ctime != 0:
                i_event.add('dtstamp').value = datetime.fromtimestamp(event.ctime, tz=None)
            else:
                i_event.add('dtstamp').value = datetime(time.time())
        return ics.serialize()


def create_calendar(calendar: CalCalendar, events: sqlalchemy.engine.ResultProxy) -> Calendar:
    this_calendar = Calendar(calendar)

    for event in events:
        this_calendar.add_event(event)

    this_calendar.limit = this_calendar.get_events_count() > 499
    return this_calendar


def extract_calendar_list(connection: sqlalchemy.engine.Connection, user: EmAccount) -> List[Calendar]:
    query = sqlalchemy.select([CalCalendar]).where(CalCalendar.user_id == user.user_id)
    calendars = connection.execute(query)
    return_cals = []
    for calendar in calendars:
        query = sqlalchemy.select([CalEvent]).where(CalEvent.calendar_id == calendar.id)
        results = connection.execute(query)
        return_cals.append(create_calendar(calendar, results))
    return return_cals


def export_calendars_from_user(connection: sqlalchemy.engine.Connection, user: EmAccount,
                               base_name: str, zimbra: ZimbraAdminConfig) -> (str, str):
    calendars = extract_calendar_list(connection, user)
    return_zimbra = ""
    return_script = ""
    for calendar in calendars:
        if not calendar.limit:
            ical = calendar.get_ical()
            filename = base_name + '.' + calendar.get_calendar().name + '.' + user.username + '.ics'
            file = open(filename, "w", encoding='utf-8')
            # file.write(ical.encode('utf-8'))
            file.write(ical)
            file.close()
            return_zimbra += "selectMailbox -A "+user.username+"\n"
            return_zimbra += "createFolder --view appointment \"/Calendar/" + calendar.get_calendar().name + "\"\n"
            return_script += "curl -k -v -u " + zimbra.login + ":" + zimbra.password + " " + zimbra.url + user.username + \
                             '/Calendar/' + urllib.parse.quote(calendar.get_calendar().name) + '?fmt=ics --upload-file \"' + \
                             filename + '\"\n'
        else:
            for portion in range(calendar.get_events_count()//499 + 1):
                ical = calendar.get_ical(portion)
                filename = base_name + '.' + calendar.get_calendar().name + '.' + user.username + '.' + str(portion) + '.ics'
                file = open(filename, "w", encoding='utf-8')
                # file.write(ical.encode('utf-8'))
                file.write(ical)
                file.close()
                return_zimbra += "selectMailbox -A " + user.username + "\n"
                return_zimbra += "createFolder --view appointment \"/Calendar/" + calendar.get_calendar().name + "\"\n"
                return_script += "curl -k -v -u " + zimbra.login + ":" + zimbra.password + " " + zimbra.url + user.username + \
                                 '/Calendar/' + urllib.parse.quote(
                    calendar.get_calendar().name) + '?fmt=ics --upload-file \"' + \
                                 filename + '\"\n'

    return return_zimbra, return_script
