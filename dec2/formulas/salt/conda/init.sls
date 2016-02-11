{%- from 'conda/settings.sls' import install_prefix, download_url with context %}

miniconda-curl:
  pkg.installed:
    - name: curl

miniconda-download:
  cmd.run:
    - name: curl {{ download_url }} > /tmp/miniconda.sh
    - unless: test -e {{ install_prefix }}
    - require:
      - pkg: miniconda-curl

miniconda-install:
  cmd.run:
    - name: bash /tmp/miniconda.sh -b -p {{ install_prefix }}
    - unless: test -e {{ install_prefix }}
    - require:
      - cmd: miniconda-download

miniconda-pip:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install pip -y -q
    - unless: test -e {{ install_prefix }}/bin/pip
    - require:
      - cmd: miniconda-install
