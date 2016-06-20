{%- from 'dask/distributed/settings.sls' import scheduler_host with context %}

/tmp/dask.distributed.debug:
    file.managed:
        - contents: |
            scheduler_host: {{ scheduler_host }}
