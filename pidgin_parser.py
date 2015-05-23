# -*- coding: utf-8 -*-
import sys
import os
import codecs
import datetime
from string import whitespace
from HTMLParser import HTMLParser


class ChatParser(HTMLParser):
    def feed(self, data, date):
        self.chat_entry = ChatEntry()
        self.chat_entry.date = date
        self.chat_entry.original = data
        self.in_b = False
        self.in_size = False
        self.in_color = False
        HTMLParser.feed(self, data)
        if 'type' in dir(self.chat_entry):
            pass

    def handle_starttag(self, tag, attrs):
        if tag == 'b':
            self.in_b = True
        elif attrs:
            if u'size' in attrs[0]:
                self.in_size = True
            elif u'color' in attrs[0]:
                self.in_color = True

    def handle_endtag(self, tag):
        if tag == 'b':
            self.in_b = False
        elif tag == 'font':
            if self.in_size:
                self.in_size = False
            else:
                self.in_color = False

    def handle_datetime(self, data):
        dt = data[1:-1].split()
        self.chat_entry.time = datetime.time(*map(int, dt[-1].split(':')))
        if len(dt) == 2:
            self.chat_entry.date = datetime.date(*map(int, dt[0].split('.')[::-1]))

    def handle_topic_or_whatever(self, data):
        pos = data.find(u'установил(а) тему:')
        if pos != -1:
            self.chat_entry.type = 'topic'
            self.chat_entry.author = data[:pos].strip()
            self.chat_entry.content = data[pos + len(u'установил(а) тему:'):].strip()

    def handle_data(self, data):
        if self.in_size:
            self.handle_datetime(data)
        elif self.in_color:
            self.chat_entry.type = 'message'
            self.chat_entry.author = data.strip()[:-1]
        elif self.in_b:
            self.handle_topic_or_whatever(data)
        elif 'type' in dir(self.chat_entry) and data not in whitespace:
            self.chat_entry.content = data.strip()


class ChatEntry():
    pass


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
        fi_lines = fi.readlines()
        for line in fi_lines:
            parser.feed(line, date)
            if 'content' in dir(parser.chat_entry):
             fo.write(parser.chat_entry.content + '<br>')   
    fo.write('</body></html>')
    fo.close()
