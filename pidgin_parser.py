import sys
import os
import codecs
from HTMLParser import HTMLParser


class MyHTMLParser(HTMLParser):
    def feed(self, data):
        self.my_data = []
        HTMLParser.feed(self, data)

    def handle_data(self, data):
        self.my_data.append(data)

parser = MyHTMLParser()


class Message:
    def __init__(self, msg_str):
        parser.feed(msg_str)
        self.data = parser.my_data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Usage: %s directory name' % sys.argv[0])

    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Directory %s was not found!' % sys.argv[1])

    directory = sys.argv[1]
    files = os.listdir(directory)
    files.sort()

    fo = codecs.open('huh.html', 'w', 'utf-8')
    fo.write('<html><head><meta http-equiv="content-type" content="text/html; charset=UTF-8"><title>Conversation</title></head><body>')
    for file_name in files:
        fi = codecs.open(directory + '/' + file_name, 'r', 'utf-8')
        fi_lines = fi.readlines()
        for line in fi_lines:
            for dt in Message(line).data:
                fo.write(dt)
            fo.write('<br>')
    fo.write('</body></html>')
    fo.close()
