#!/usr/bin/pyhon
"""
  This script provides a feature specific HTTP Server using CherryPy.
  It serves GET requests for one predefinied html and one css file.

  The html provides a form with a file select input button, and a submit
  button which triggers the file upload and processing .

  The file is submmited to the POST handler for the "/convert" url.
  The input file, expected to be an AsciiDoc, is converted to PDF
  running asciidoctor and dblatex in a temporary build location.
  The resulting PDF is return on the POST reply, and the temporary build
  directory removed.

  The code is mostly based on the documentation sample for file uploading:
  https://cherrypy.readthedocs.io/en/3.3.0/progguide/files/uploading.html
"""


from tempfile import mkdtemp
from os.path import join, dirname
from os import getcwd

# Keep Python2/Python3 compatibility
try:
    from commands import getstatusoutput
except ImportError:
    from subprocess import getstatusoutput

import shutil
from cherrypy.lib.static import serve_file
import cherrypy

LOCALDIR = dirname(__file__)
ABSDIR = join(getcwd(), LOCALDIR)

class Root(object):
    """ CherryPy application-object handling the HTTP Requests """

    @cherrypy.expose
    def index(self):
        """ Return the index.html """
        return serve_file(join(ABSDIR, 'webroot', 'index.html'))

    @cherrypy.expose
    def convert(self, myfile):
        """ Process the adoc file, return the resulting PDF or an HTML on error """
        error_msg = """<html>
        <body>
            %s
        </body>
        </html>"""
        if not myfile.filename.lower().endswith('.adoc'):
            return error_msg % ('Input file must end mut be an.adoc')

        input_file_data = myfile.file.read()
        size = len(input_file_data)

        if size == 0:  # Do not handle files > 128k
            return error_msg % ('Input file is empty')

        if size > 128*1024:  # Do not handle files > 128k
            return error_msg % ('Input file must not be > 128k')

        build_dir = mkdtemp()
        fname_adoc = join(build_dir, 'input.adoc')
        fname_xml = join(build_dir, 'input.xml')
        fname_pdf = join(build_dir, 'output.pdf')

        with open(fname_adoc, 'wb') as adoc_file:
            adoc_file.write(input_file_data)

        cmd = 'asciidoctor -b docbook -a article %s -o %s' % (fname_adoc, fname_xml)
        exit_code, output = getstatusoutput(cmd)

        if exit_code != 0:
            shutil.rmtree(build_dir)
            return error_msg % ("Failed running asciidoctor<br>"+output.replace("\n", '<br>'))

        cmd = 'dblatex -P latex.encoding=utf8 %s -o %s' % (fname_xml, fname_pdf)
        exit_code, output = getstatusoutput(cmd)

        if exit_code != 0:
            shutil.rmtree(build_dir)
            return error_msg % ("Failed running dblatex<br>"+output.replace("\n", '<br>'))

        pdf_result_fname = myfile.filename.rsplit('.', 1)[0]+".pdf"
        result = serve_file(fname_pdf, disposition='attachment', \
            name=pdf_result_fname)
        shutil.rmtree(build_dir)
        return result


def main():
    """ Setup the application config, and start the http server engine """
    cherrypy.config.update(join(ABSDIR, 'http_server.conf'))
    app = cherrypy.tree.mount(Root())
    confdict = {
        '/css/bootstrap.min.css' : {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': join(ABSDIR, 'webroot', 'css', 'bootstrap.min.css')
        }
    }
    app.merge(confdict)
    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    main()
