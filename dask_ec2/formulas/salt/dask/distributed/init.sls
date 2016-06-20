{%- from 'conda/settings.sls' import install_prefix with context -%}

include:
  - conda
  - system.base

dask-install:
  pip.installed:
    - name: dask
    - bin_env: {{ install_prefix }}/bin/pip
    - require:
      - sls: conda

bokeh-install:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install bokeh -y -q
    - require:
      - sls: conda

distributed-install:
  pip.installed:
    - name: distributed
    - upgrade: true
    - bin_env: {{ install_prefix }}/bin/pip
    - require:
      - sls: conda

update-pandas:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda update pandas
    - require:
      - pip: distributed-install
