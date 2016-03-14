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

remove-anconda:
  # LOLZ
  cmd.run:
    - name: {{ install_prefix }}/bin/conda remove anaconda || true
    - require:
      - cmd: miniconda-install

miniconda-pip:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install pip -y -q
    - unless: test -e {{ install_prefix }}/bin/pip
    - require:
      - cmd: miniconda-install

/etc/profile.d/conda.sh:
  file.managed:
    - source: salt://conda/templates/conda.sh
    - user: root
    - group: root
    - mode: 666
    - template: jinja
    - require:
      - cmd: miniconda-install
