{%- from 'conda/settings.sls' import install_prefix, download_url with context %}

anaconda-curl:
  pkg.installed:
    - name: curl

anaconda-download:
  cmd.run:
    - name: curl -k {{ download_url }} > /tmp/anaconda.sh
    - unless: test -e {{ install_prefix }}
    - require:
      - pkg: anaconda-curl

anaconda-install:
  cmd.run:
    - name: bash /tmp/anaconda.sh -b -p {{ install_prefix }}
    - unless: test -e {{ install_prefix }}
    - require:
      - cmd: anaconda-download

remove-anconda:
  # LOLZ
  cmd.run:
    - name: {{ install_prefix }}/bin/conda remove anaconda -q -y || true
    - require:
      - cmd: anaconda-install

anaconda-pip:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install pip -y -q
    - unless: test -e {{ install_prefix }}/bin/pip
    - require:
      - cmd: anaconda-install

/etc/profile.d/conda.sh:
  file.managed:
    - source: salt://conda/templates/conda.sh
    - user: root
    - group: root
    - mode: 666
    - template: jinja
    - require:
      - cmd: anaconda-install
