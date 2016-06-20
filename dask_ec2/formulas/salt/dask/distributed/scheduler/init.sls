{%- from 'supervisor/settings.sls' import supervisorctl, supervisord_conf, conf_d with context -%}

include:
  - supervisor
  - dask.distributed

dscheduler.conf:
  file.managed:
    - name: {{ conf_d }}/dscheduler.conf
    - source: salt://dask/distributed/templates/dscheduler.conf
    - template: jinja
    - makedirs: true
    - require:
      - sls: supervisor
      - sls: dask.distributed

dscheduler-update-supervisor:
  cmd.wait:
    - name: {{ supervisorctl }} -c {{ supervisord_conf }} update && sleep 2
    - watch:
      - file: dscheduler.conf

dscheduler-running:
  supervisord.running:
    - name: dscheduler
    - watch:
      - sls: dask.distributed
      - file: dscheduler.conf
      - cmd: dscheduler-update-supervisor
