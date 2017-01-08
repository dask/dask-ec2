{%- from 'supervisor/settings.sls' import supervisorctl, supervisord_conf, conf_d with context -%}

include:
  - supervisor
  - dask.distributed

dask-scheduler.conf:
  file.managed:
    - name: {{ conf_d }}/dask-scheduler.conf
    - source: salt://dask/distributed/templates/dask-scheduler.conf
    - template: jinja
    - makedirs: true
    - require:
      - sls: supervisor
      - sls: dask.distributed

dask-scheduler-update-supervisor:
  cmd.wait:
    - name: {{ supervisorctl }} -c {{ supervisord_conf }} update && sleep 2
    - watch:
      - file: dask-scheduler.conf

dask-scheduler-running:
  supervisord.running:
    - name: dask-scheduler
    - watch:
      - sls: dask.distributed
      - file: dask-scheduler.conf
      - cmd: dask-scheduler-update-supervisor
