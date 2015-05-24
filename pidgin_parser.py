# -*- coding: utf-8 -*-
import sys
import os
import codecs
import datetime
from string import whitespace
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Integer, DateTime, Text, String, Column

name2codepoint['apos'] = 0x0027
db = declarative_base()

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
        self.chat_entry.time = datetime.time(*map(int, dt[-1].split(':')))
        if len(dt) == 2:
            self.chat_entry.date = datetime.date(*map(int, dt[0].split('.')[::-1]))
        self.chat_entry.datetime = datetime.datetime.combine(
                self.chat_entry.date, self.chat_entry.time)

    def handle_topic_or_whatever(self, data):
        pos = data.find(u'тему: ')
        if pos != -1:
            self.chat_entry.type = 'topic'
            self.chat_entry.author = data[:pos].strip()
            self.chat_entry.content +=\
                    data[pos + len(u'тему: '):]
        else:
            self.chat_entry.content += data

    def handle_data(self, data):
        if 'title' in self.context or 'h3' in self.context:
            pass
        elif 'size' in self.context:
            self.handle_datetime(data)
        elif 'color' in self.context:
            self.chat_entry.type = 'message'
            self.chat_entry.author = data.strip()[:-1]
        elif 'b' in self.context:
            self.handle_topic_or_whatever(data)
        else:
            self.chat_entry.content += data.strip()

    def handle_entityref(self, name):
        self.chat_entry.content +=  unichr(name2codepoint[str(name)])


class ChatEntry(db):
    __tablename__ = 'chat_entries'

    id = Column(Integer, primary_key=True)
    type = Column(String(7))
    author = Column(String(400))
    datetime = Column(DateTime)
    content = Column(Text)
    original = Column(Text)

    def __init__(self, original, date):
        self.type = None
        self.content = ''
        self.original = original
        self.date = date

    def __eq__(self, other):
        return type(self) == type(other) and\
                self.datetime == other.datetime and\
                self.author == other.author and\
                self.content == other.content and\
                self.type == other.type


    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.original
    
    def text(self):
        normal_date = '{:02d}.{:02d}.{:04d}'.format(
                self.datetime.day, self.datetime.month, self.datetime.year)
        if self.type == 'message':
            template = u'({} {}) {}: {}'
        else:
            template = u'({} {}) {} установил(а) тему: {}'
        return template.format(normal_date, self.datetime.time,
                self.author, self.content)

    def html(self):
        return self.original.replace('#16569E', '#A82F2F')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Usage: %s directory name' % sys.argv[0])

    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Directory %s was not found!' % sys.argv[1])

    directory = sys.argv[1]
    files = os.listdir(directory)
    files.sort()
    parser = ChatParser()
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session() 
    # db.metadata.create_all(engine) 

    for file_name in files:
        date = datetime.date(*map(int, file_name[:10].split('-')))
        fi = codecs.open(directory + '/' + file_name, 'r', 'utf-8')
        fi_lines = fi.read().split('<br/>\n')
        for line in fi_lines:
            h3_pos = line.rfind('</h3>')
            if h3_pos != -1:
                line = line[h3_pos + len('</h3>'):]
                if line[0] == '\n':
                    line = line[1:]
            chat_entry = ChatEntry(line, date)
            parser.feed(chat_entry)
            if chat_entry.type is not None and\
                    session.query(ChatEntry).filter_by(
                    type=chat_entry.type,
                    datetime=chat_entry.datetime,
                    author=chat_entry.author).first() is None:

                session.add(chat_entry)
        session.commit()

    fo_html = codecs.open('huh.html', 'w', 'utf-8')
    fo_text = codecs.open('huh', 'w', 'utf-8')
    fo_html.write('<html><head><meta http-equiv="content-type" content="text/html; charset=UTF-8"><title>Conversation</title></head><body>')
    for chat_entry in session.query(ChatEntry).order_by(ChatEntry.datetime):
        # fo_html.write(('<b>{}</b><br>\n').format(chat_entry.type))   
        fo_html.write(chat_entry.html().replace('\n', '<br>'))   
        fo_html.write('<br>\n')
        fo_text.write(chat_entry.text())
        fo_text.write('\n')
    fo_html.write('</body></html>')
    fo_html.close()
    fo_text.close()
