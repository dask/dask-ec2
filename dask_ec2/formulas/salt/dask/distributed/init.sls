{%- from 'conda/settings.sls' import install_prefix with context -%}
{%- from 'dask/distributed/settings.sls' import source_install with context -%}

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
    - name: {{ install_prefix }}/bin/conda install dask distributed fastparquet -y -q -c conda-forge
    - require:
      - sls: conda

{% if source_install %}
# install dask (above) to get dependencies then install from git
source-dask-install:
  pip.installed:
    - name: git+https://github.com/dask/dask
    - bin_env: {{ install_prefix }}/bin/pip
    - require:
      - sls: conda

source-distributed-install:
  pip.installed:
    - name: git+https://github.com/dask/distributed
    - bin_env: {{ install_prefix }}/bin/pip
    - require:
      - sls: conda

{% endif %}


update-pandas:
  cmd.run:
    - name: {{ install_prefix }}/bin/conda update pandas -y -q
    - require:
      - update-pyopenssl
