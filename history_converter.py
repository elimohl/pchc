#!/usr/bin/env python


import argparse
import os
import codecs
import datetime
from html.parser import HTMLParser
from html.entities import name2codepoint

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Integer, DateTime, Text, String, Column


name2codepoint['apos'] = 0x0027
TOPIC_TEMPLATE = '({date} {time}) {author} установил(а) тему: {text}'
TOPIC_PREFIX_END = 'тему: '


class ChatParser(HTMLParser):
    def feed(self, chat_entry):
        self.context = set()
        self.chat_entry = chat_entry
        HTMLParser.feed(self, chat_entry.original)

    def handle_starttag(self, tag, attrs):
        if tag != 'font':
            self.context.add(tag)
        elif attrs:
            if 'size' in attrs[0]:
                self.context.add('size')
            elif 'color' in attrs[0]:
                self.context.add('color')

    def handle_endtag(self, tag):
        if tag != 'font':
            self.context.discard(tag)
        else:
            if 'size' in self.context:
                self.context.discard('size')
            else:
                self.context.discard('color')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.chat_entry.content += '\n'

    def handle_datetime(self, data):
        dt = data[1:-1].split()
        self.chat_entry.time = datetime.time(*list(map(int, dt[-1].split(':'))))
        if len(dt) == 2:
            self.chat_entry.date = datetime.date(*list(map(int, dt[0].split('.')[::-1])))
        self.chat_entry.datetime = datetime.datetime.combine(
            self.chat_entry.date, self.chat_entry.time)

    def handle_topic_or_whatever(self, data):
        pos = data.find(TOPIC_PREFIX_END)
        if pos != -1:
            self.chat_entry.type = 'topic'
            author_end_pos = data[:pos].rstrip().rfind(' ')
            if author_end_pos != -1:
                self.chat_entry.author = data[1:author_end_pos]
            self.chat_entry.content += data[pos + len(TOPIC_PREFIX_END):]
        else:
            self.chat_entry.content += data

    def handle_data(self, data):
        if 'title' in self.context or 'h3' in self.context:
            pass
        elif 'size' in self.context:
            self.handle_datetime(data)
        elif 'color' in self.context:
            author = data.strip()
            if author[:3] == '***':
                self.chat_entry.type = 'me-message'
                self.chat_entry.author = author[3:]
            else:
                self.chat_entry.type = 'message'
                self.chat_entry.author = author[:-1]
        elif 'b' in self.context:
            self.handle_topic_or_whatever(data)
        else:
            self.chat_entry.content += data.strip()

    def handle_entityref(self, name):
        self.chat_entry.content += chr(name2codepoint[str(name)])


db = declarative_base()


class ChatEntry(db):
    __tablename__ = 'chat_entries'

    id = Column(Integer, primary_key=True)
    type = Column(String(10))
    author = Column(String(400))
    datetime = Column(DateTime)
    content = Column(Text)
    original = Column(Text)

    def __init__(self, original, date):
        self.type = None
        self.content = ''
        self.original = original
        self.date = date

    def __repr__(self):
        return self.original.encode('utf8')

    def text(self):
        normal_date = '{:02d}.{:02d}.{:04d}'.format(
            self.datetime.day, self.datetime.month, self.datetime.year)
        if self.type == 'message':
            template = '({date} {time}) {author}: {text}'
        elif self.type == 'me-message':
            template = '({date} {time}) ***{author} {text}'
        else:
            template = TOPIC_TEMPLATE
        return template.format(date=normal_date,
                               time=self.datetime.time(),
                               author=self.author,
                               text=self.content)

    def html(self):
        return self.original.replace('#16569E', '#A82F2F')  # to not highlight one's username


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        description='convert pidgin conference history to more convinient formats')
    argparser.add_argument('dir', help='source directory')
    argparser.add_argument(
            'format',
            choices=['html', 'single-html', 'single-text', 'text', 'db', 'all'],
            help='How to store the result.'
                 '"single" means that the result will be stored in one text/html file'
                 'otherwise there will be one file per day',
            )
    argparser.add_argument(
            '-n',
            '--name',
            help='set the name for the result (default name is created from source directory name)',
            )
    args = argparser.parse_args()

    directory = args.dir
    files = os.listdir(directory)

    parser = ChatParser()
    name = args.name
    if not name:
        name = directory.strip('/').split('/')[-1]
        at_pos = name.find('@')
        if at_pos != -1:
            name = name[:at_pos]
        else:
            name = name + '_history'

    if args.format in ('db', 'all'):
        engine = create_engine('sqlite:///{}.db'.format(name))
    else:
        engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    db.metadata.create_all(engine)

    for file_name in files:
        date = datetime.date(*list(map(int, file_name[:10].split('-'))))
        fi = codecs.open(directory + '/' + file_name, 'r', 'utf-8')
        fi_lines = fi.read().split('<br/>\n')
        for line in fi_lines:
            # remove title
            h3_pos = line.rfind('</h3>')
            if h3_pos != -1:
                line = line[h3_pos + len('</h3>'):]
                if line[0] == '\n':
                    line = line[1:]

            chat_entry = ChatEntry(line, date)
            parser.feed(chat_entry)
            # sometimes i have equivalent messages with little time distinction
            if chat_entry.type is not None and\
                    session.query(ChatEntry).filter(
                    ChatEntry.type == chat_entry.type,
                    ChatEntry.author == chat_entry.author,
                    ChatEntry.content == chat_entry.content,
                    ChatEntry.datetime >= chat_entry.datetime - datetime.timedelta(seconds=2),
                    ChatEntry.datetime <= chat_entry.datetime + datetime.timedelta(seconds=2)
                    ).first() is None:

                session.add(chat_entry)
        session.commit()

    if args.format in ('single-html', 'all'):
        fo_html = codecs.open('{}.html'.format(name), 'w', 'utf-8')
        fo_html.write('<html><head><meta http-equiv="content-type"'
                      'content="text/html; charset=UTF-8">'
                      '<title>Conversation</title></head><body>')
        for chat_entry in session.query(ChatEntry).order_by(ChatEntry.datetime):
            fo_html.write(chat_entry.html().replace('\n', '<br>'))
            fo_html.write('<br>\n')
        fo_html.write('</body></html>')
        fo_html.close()
        session.close()

    if args.format in ('single-text', 'all'):
        fo_text = codecs.open(name, 'w', 'utf-8')
        for chat_entry in session.query(ChatEntry).order_by(ChatEntry.datetime):
            fo_text.write(chat_entry.text())
            fo_text.write('\n')
        fo_text.close()
        session.close()

    if args.format in ('text', 'html', 'all'):
        day = datetime.datetime(*list(map(int, files[0][:10].split('-'))))
        last_day = datetime.datetime(*list(map(int, files[-1][:10].split('-'))))
        while day <= last_day:
            entries = session.query(ChatEntry).filter(
                ChatEntry.datetime >= day,
                ChatEntry.datetime < day + datetime.timedelta(days=1)).order_by(ChatEntry.datetime).all()
            if entries:
                if args.format in ('html', 'all'):
                    if not os.path.exists('{}_html'.format(name)):
                        os.makedirs('{}_html'.format(name))
                    fo_html = codecs.open('{0}_html/{1}_{0}.html'.format(name, day.date()), 'w', 'utf-8')
                    fo_html.write('<html><head><meta http-equiv="content-type"'
                                  'content="text/html; charset=UTF-8">'
                                  '<title>Conversation at {}</title></head><body>'.format(day.date()))
                    for chat_entry in entries:
                        fo_html.write(chat_entry.html().replace('\n', '<br>'))
                        fo_html.write('<br>\n')
                    fo_html.write('</body></html>')
                    fo_html.close()
                if args.format in ('text', 'all'):
                    if not os.path.exists('{}_text'.format(name)):
                        os.makedirs('{}_text'.format(name))
                    fo_text = codecs.open('{0}_text/{1}_{0}'.format(name, day.date()), 'w', 'utf-8')
                    for chat_entry in entries:
                        fo_text.write(chat_entry.text())
                        fo_text.write('\n')
                    fo_text.close()
            day += datetime.timedelta(days=1)
        session.close()
