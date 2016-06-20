{%- from 'conda/settings.sls' import install_prefix with context %}

/tmp/conda.debug:
  file.managed:
    - contents: |
        install_prefix: {{ install_prefix }}
