{%- from 'conda/settings.sls' import install_prefix with context -%}

include:
  - conda

dask-install:
  pip.installed:
    - name: dask
    - bin_env: {{ install_prefix }}/bin/pip
    - require:
      - sls: conda

distributed-install:
  pip.installed:
    - name: distributed
    - bin_env: {{ install_prefix }}/bin/pip
    - require:
      - sls: conda
