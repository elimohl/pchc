# -*- coding: utf-8 -*-
import sys
import os
import codecs
import datetime
from string import whitespace
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint


name2codepoint['apos'] = 0x0027


class ChatParser(HTMLParser):
    def feed(self, data, date):
        self.chat_entry = ChatEntry()
        self.chat_entry.date = date
        self.chat_entry.original = data
        # self.in = {tag: False for tag in ('h3', 'title', 'font', 'b')}
        self.context = set()
        HTMLParser.feed(self, data)
        if self.chat_entry.type is not None:
            pass

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
            print data
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


class ChatEntry():
    def __init__(self):
        self.type = None
        self.content = ''

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Usage: %s directory name' % sys.argv[0])

    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Directory %s was not found!' % sys.argv[1])

    directory = sys.argv[1]
    files = os.listdir(directory)
    files.sort()
    parser = ChatParser()

    fo = codecs.open('huh.html', 'w', 'utf-8')
    fo.write('<html><head><meta http-equiv="content-type" content="text/html; charset=UTF-8"><title>Conversation</title></head><body>')
    for file_name in files:
        date = datetime.date(*map(int, file_name[:10].split('-')))
        fi = codecs.open(directory + '/' + file_name, 'r', 'utf-8')
        fi_lines = fi.read().split('<br/>\n')
        for line in fi_lines:
            parser.feed(line, date)
            if parser.chat_entry.type is not None:
             fo.write('<b>' + parser.chat_entry.type + '</b><br>')
             fo.write(parser.chat_entry.content.replace('\n', '<br>'))   
             fo.write('<br>\n')
    fo.write('</body></html>')
    fo.close()
