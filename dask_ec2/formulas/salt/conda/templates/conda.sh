{%- from 'conda/settings.sls' import install_prefix with context -%}

export PATH="{{ install_prefix }}/bin:$PATH"
