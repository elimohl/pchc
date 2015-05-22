from bs4 import BeautifulSoup
from HTMLParser import HTMLParser
import re
import codecs
import sys
import os

if len(sys.argv) < 2:
    sys.exit('Usage: %s directory name' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
    sys.exit('ERROR: Directory %s was not found!' % sys.argv[1])

directory = sys.argv[1]
files = os.listdir(directory)
files.sort()


class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print "Encountered a start tag:", tag

    def handle_endtag(self, tag):
        print "Encountered an end tag :", tag

    def handle_data(self, data):
        print "Encountered some data  :", data

fi = open('huh.html', 'r')
parser = MyHTMLParser()
parser.feed(fi.read())
fi.close()


def simple_conc(files):
    fo = codecs.open('huh.html', 'w', 'utf-8')
    fo.write('<html><head><meta http-equiv="content-type" content="text/html; charset=UTF-8"><title>Conversation</title></head><body>')
    lines = []
    for fi_name in files:
        fi = open(directory + '/' + fi_name, 'r')
        fi_lines = fi.readlines()

    fo.write('</body></html>')
    fo.close()


def html2text(html):
    p = re.compile('<br/>(?=[^\n])')
    html = p.sub('<br>\n', html)
    bs = BeautifulSoup(html)
    return bs.body.text
