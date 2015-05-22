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
        print self.data


if __name__ == 'main':
    if len(sys.argv) < 2:
        sys.exit('Usage: %s directory name' % sys.argv[0])

    if not os.path.exists(sys.argv[1]):
        sys.exit('ERROR: Directory %s was not found!' % sys.argv[1])

    directory = sys.argv[1]
    files = os.listdir(directory)
    files.sort()

    fo = codecs.open('huh.html', 'w', 'utf-8')
    fo.write('<html><head><meta http-equiv="content-type" content="text/html; charset=UTF-8"><title>Conversation</title></head><body>')
    lines = []
    for file_name in files:
        fi = codecs.open(directory + '/' + file_name, 'r', 'utf-8')
        fi_lines = fi.readlines()
        if not fi_lines:
            continue
        if fi_lines[0].find('<html>') != -1:
            fi_lines = fi_lines[1:]
        if fi_lines[-1].find('</html>') != -1:
            fi_lines = fi_lines[:-1]
        fi.close()
        if not fi_lines:
            continue
        for i in range(1, 20):
            if i > len(lines) or fi_lines[0] == lines[-i]:
                lines += fi_lines[i:]
                break
        lines += fi_lines

    for line in lines:
        fo.write(line)

    fo.write('</body></html>')
    fo.close()
