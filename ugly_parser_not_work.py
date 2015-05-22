import sys
import os
import codecs

if len(sys.argv) < 2:
    sys.exit('Usage: %s directory name' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
    sys.exit('ERROR: Directory %s was not found!' % sys.argv[1])

directory = sys.argv[1]
files = os.listdir(directory)
files.sort()

class Message:
    __init__(self, msg_str):
        self.time = None
        self.author = None
        self.text = None
        position = msg_str.find("<font size="2">")
        if position != -1:
            position = msg_str[position:].find(')')
            if position != -1:
                time = msg_str[position - 8:position]
                position


def equal_messages(msg1, msg2):
    if autho


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
        if i > len(lines) or equal_messages(fi_lines[0], lines[-i]):
            lines += fi_lines[i:]
            break
    lines += fi_lines

for line in lines:
    fo.write(line)

fo.write('</body></html>')
fo.close()
