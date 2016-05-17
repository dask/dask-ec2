{%- from 'conda/settings.sls' import install_prefix with context %}

include:
  - conda

jupyter-install:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install jupyter -y -q 
    - require:
      - sls: conda
