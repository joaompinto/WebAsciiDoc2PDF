FROM centos:centos7

MAINTAINER João Pinto <lamego.pinto@gmail.com>

# Ruby provides  asciidoctor GEM and graphviz for UML diagrams support
RUN yum install -y ruby graphviz 

# dblates provides the dockbook xml to pdf conversion
RUN yum install -y dblatex texlive-ucs

# CherryPy provides the HTTP server engine
RUN yum install -y python-cherrypy

# The following extra packages from EPEL are required for dbalatext's utf8 encoding support
RUN yum install -y \
  "https://dl.fedoraproject.org/pub/epel/7/x86_64/t/texlive-cyrillic-svn23396.0-41.el7.noarch.rpm" \
  "https://dl.fedoraproject.org/pub/epel/7/x86_64/t/texlive-cyrillic-bin-svn29349.0-41.el7.noarch.rpm" \
  "https://dl.fedoraproject.org/pub/epel/7/x86_64/t/texlive-cyrillic-bin-bin-svn27329.0-41.el7.noarch.rpm"

RUN gem install asciidoctor asciidoctor-diagram

RUN useradd -m webuser
RUN mkdir -p /usr/local/http_server /usr/local/http_server/webroot/css
RUN mkdir -p /usr/local/http_server/log && chown webuser /usr/local/http_server/log 

COPY webroot/index.html /usr/local/http_server/webroot 
COPY webroot/css/bootstrap.min.css /usr/local/http_server/webroot/css/
COPY http_server.conf /usr/local/http_server
COPY http_server.py /usr/local/http_server

WORKDIR /usr/local/http_server/
USER webuser
ENTRYPOINT python http_server.py

# The port on this line must match the http port set on http_server.conf
EXPOSE 8080