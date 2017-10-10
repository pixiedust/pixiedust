FROM markwatsonatx/pixiedust-base-python35:latest

MAINTAINER Mark Watson <markwatsonatx@gmail.com>

WORKDIR /home/root
ADD startup.sh ./

RUN mkdir -p /root/pixiedust/bin

WORKDIR /

WORKDIR /pixiedust
#RUN pip install -e ./
#RUN jupyter pixiedust install --silent --spark=2.1.0
#RUN jupyter pixiedust install --silent --spark=2.0.2
#RUN jupyter pixiedust install --silent --spark=1.6.3
#RUN cp /root/pixiedust/notebooks/*.ipynb /usr/notebooks
