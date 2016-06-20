{%- from 'supervisor/settings.sls' import supervisorctl, supervisord_conf, conf_d with context %}

include:
  - supervisor
  - dask.distributed

dworker.conf:
  file.managed:
    - name: {{ conf_d }}/dworker.conf
    - source: salt://dask/distributed/templates/dworker.conf
    - template: jinja
    - makedirs: true
    - require:
      - sls: supervisor
      - sls: dask.distributed

dworker-update-supervisor:
  cmd.wait:
    - name: {{ supervisorctl }} -c {{ supervisord_conf }} update && sleep 2
    - watch:
      - file: dworker.conf

dworker-running:
  supervisord.running:
    - name: dworker
    - watch:
      - sls: dask.distributed
      - file: dworker.conf
      - cmd: dworker-update-supervisor
