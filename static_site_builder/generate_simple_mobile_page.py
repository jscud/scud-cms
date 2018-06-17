# Generates a simple web page with headings for sections and a table of
# contents at the top. Section headings are marked with a % symbol followed
# by a short code that should be unique in the page. The text on the next line
# after the heading marker (%shortcode) is used as the title for that section.
#
# Here's an example. The following input produces a page with two headings.
#
# %heading1
# Title for the first heading
# Content in the first section goes here.
#
# %heading2
# Second section title
# This is the content in the second section.
#
# %footer
# Made by me.

import sys

PAGE_HEADER = '''
<!doctype html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
     body {
       font-family: 'Roboto', 'San Francisco', Helvetica, Arial, san-serif;
       background-color: #f5f5f5;
     }
     .footer {
       text-align: center;
       font-size: 70%;
     }
     .card {
       max-width: 400px;
       margin-left: auto;
       margin-right: auto;
       margin-bottom: 4px;
       background-color: #fff;
       padding: 5px 10px 5px 10px;
       border-radius: 3px;
     }
     .elev1 {
       box-shadow: 0 2px 2px 0 rgba(0,0,0,0.14),
                   0 3px 1px -2px rgba(0,0,0,0.12),
                   0 1px 5px 0 rgba(0,0,0,0.2);
     }
     .elev2 {
       box-shadow: 0 4px 5px 0 rgba(0,0,0,0.14),
                   0 1px 10px 0 rgba(0,0,0,0.12),
                   0 2px 4px -1px rgba(0,0,0,0.3);
     }
    </style>
  </head>
  <body>'''

PAGE_FOOTER = '''
  </body>
</html>
'''

class SimplePage:
    def __init__(self):
        self.headings = []
        self.lines = []
        self.footer = '';
    
    def parse_file(self, source_file):
        reading_heading = False
        reading_footer = False
        heading_short_code = ''
        for line in source_file.readlines():
            if line.startswith('%footer'):
                reading_footer = True
            elif reading_footer:
                self.footer = line.strip()
                reading_footer = False
            elif line.startswith('%'):
                heading_short_code = line[1:]
                reading_heading = True
            elif reading_heading:
                self.headings.append('<a href="#%s">%s</a><br>' % (
                    heading_short_code.strip(), line.strip()))
                self.lines.append(
                    '</div><div class="card elev1"><h2 id="%s">%s</h2>' % (
                        heading_short_code.strip(), line.strip()))
                reading_heading = False
            else:
                self.lines.append('%s<br>' % line.strip())

    def print_header(self):
        print(PAGE_HEADER)

    def print_html(self):
        print('<div class="card elev2">')
        for i in xrange(len(self.headings)):
            print(self.headings[i])
        for i in xrange(len(self.lines)):
            print(self.lines[i])
        print('</div>')

    def print_footer(self):
        if self.footer:
            print('<div class="footer">%s</div>' % self.footer)
        print(PAGE_FOOTER)


def main():
  if len(sys.argv) < 2:
      print('You must provide a file to read.')
      print('For example, run %s filename.txt' % sys.argv[0])
      return

  source = open(sys.argv[1])
  page = SimplePage()
  page.parse_file(source)
  page.print_header()
  page.print_html()
  page.print_footer()
  source.close()


if __name__ == '__main__':
    main()

