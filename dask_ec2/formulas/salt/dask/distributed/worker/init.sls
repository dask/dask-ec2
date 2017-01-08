{%- from 'supervisor/settings.sls' import supervisorctl, supervisord_conf, conf_d with context %}

include:
  - supervisor
  - dask.distributed

dask-worker.conf:
  file.managed:
    - name: {{ conf_d }}/dask-worker.conf
    - source: salt://dask/distributed/templates/dask-worker.conf
    - template: jinja
    - makedirs: true
    - require:
      - sls: supervisor
      - sls: dask.distributed

dask-worker-update-supervisor:
  cmd.wait:
    - name: {{ supervisorctl }} -c {{ supervisord_conf }} update && sleep 2
    - watch:
      - file: dask-worker.conf

dask-worker-running:
  supervisord.running:
    - name: dask-worker
    - watch:
      - sls: dask.distributed
      - file: dask-worker.conf
      - cmd: dask-worker-update-supervisor
