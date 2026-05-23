ARG BASE_IMAGE=python:3.11-slim-bookworm
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN find /etc/apt -type f \( -name '*.sources' -o -name '*.list' \) -exec sed -i 's|http://deb.debian.org/debian|https://deb.debian.org/debian|g' {} + \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get install -y --fix-missing --no-install-recommends \
        build-essential \
        git \
        curl \
        ca-certificates \
        nodejs \
        npm \
        libpq-dev \
        texlive-xetex \
        texlive-lang-chinese \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel

RUN pip install \
    jupyterlab \
    notebook \
    ipykernel \
    jupyterlab-lsp \
    pandas \
    numpy \
    scipy \
    statsmodels \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    altair \
    bokeh \
    pyarrow \
    openpyxl \
    xlsxwriter \
    xlrd \
    lxml \
    sqlalchemy \
    psycopg2-binary \
    duckdb \
    connectorx \
    h5py \
    tables \
    zarr \
    ipywidgets \
    jupyterlab_widgets \
    rdkit \
    py3Dmol \
    mols2grid \
    polars \
    networkx \
    biopython \
    gseapy \
    pyfaidx \
    pysam \
    lifelines \
    umap-learn

RUN pip install pypandoc_binary \
    && ln -sf /usr/local/lib/python3.11/site-packages/pypandoc/files/pandoc /usr/local/bin/pandoc \
    && chmod +x /usr/local/lib/python3.11/site-packages/pypandoc/files/pandoc

COPY start-services.sh /usr/local/bin/start-services
RUN chmod +x /usr/local/bin/start-services

EXPOSE 8888 3000

CMD ["start-services"]
