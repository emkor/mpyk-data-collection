FROM debian:9-slim

RUN apt-get update && apt-get install --no-install-recommends -y git zip curl jq python3 python3-setuptools python3-wheel python3-pip

RUN pip3 install --no-cache-dir b2

RUN git clone https://github.com/emkor/mpyk.git \
    && pip3 install -r mpyk/requirements.txt \
    && chmod u+x mpyk/mpyk.py \
    && ln -s mpyk/mpyk.py /usr/local/bin/mpyk

RUN git clone https://github.com/emkor/mpyk-data-collection.git \
    && chmod u+x mpyk-data-collection/*.sh

RUN python3 --version && pip3 --version && jq --version && b2 version

ENTRYPOINT ["bash"]