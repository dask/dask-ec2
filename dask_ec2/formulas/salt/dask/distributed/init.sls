{%- from 'conda/settings.sls' import install_prefix with context -%}

include:
  - conda
  - system.base

update-pyopenssl:
  cmd.run:
    - name: CONDA_SSL_VERIFY=false {{ install_prefix }}/bin/conda update pyopenssl -y -q
    - require:
      - sls: conda

bokeh-install:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install bokeh -y -q
    - require:
      - sls: conda

dask-install:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda install dask distributed -y -q -c conda-forge
    - require:
      - sls: conda


update-pandas:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda update pandas -y -q
    - require:
      - update-pyopenssl
