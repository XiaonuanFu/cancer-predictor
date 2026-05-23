FROM broadinstitute/gatk:4.6.1.0

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    git \
    samtools \
    bcftools \
    python3 \
    python3-pip \
    nano \
    less \
    htop

RUN curl -s https://get.nextflow.io | bash && \
    mv nextflow /usr/local/bin/

WORKDIR /data

CMD ["bash"]
