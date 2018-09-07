#The MIT License (MIT)

#Copyright (c) 2018 Louis-Philippe Querel l_querel@encs.concordia.ca lquerel@gmail.com
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#and associated documentation files (the "Software"), to deal in the Software without restriction,
#including without limitation the rights to use, copy, modify, merge, publish, distribute,
#sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or
#substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

FROM ubuntu:14.04

RUN apt-get update

#setup git
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get install git -y

#setup python
RUN apt-get install python python-pip python-dev libpq-dev -y
RUN pip install psycopg2 gitpython subprocess32

#setup jdk
#RUN apt-get install openjdk-7-jdk -y # Will probably need to use the oracle one
RUN apt-get install maven wget -y # Will probably need to use the oracle one

#setup maven

#setup toif
WORKDIR /opt
COPY libraries .
RUN tar -zxvf kdmanalytics-oss-toif-2.1.0.linux.gtk.x86_64.tar.gz; mv toif-2.1.0 ./toif
#RUN apt-get install wget
#RUN wget https://github.com/KdmAnalytics/toif/archive/v2.1.0.zip
#RUN unzip v2.1.0.zip;

RUN tar -zxvf findbugs-3.0.1.tar.gz; mv findbugs-3.0.1 ./findbugs; cp findsecbugs-plugin-1.8.0.jar ./findbugs/lib
RUN unzip jlint-3.1.2.zip; mv jlint-3.1.2 ./jlint

RUN rm *.tar.gz *.zip

#setup findbugs

#setup jlint


WORKDIR /usr/src/app

#COPY . .



#CMD [ "python", "wg_service.py" ]

