{%- from 'jupyter/settings.sls' import jupyter_config_dir, notebooks_dir, user with context %}
{%- from 'supervisor/settings.sls' import supervisorctl, supervisord_conf, conf_d with context %}

include:
  - jupyter
  - supervisor

jupyter-notebook.conf:
  file.managed:
    - name: {{ conf_d }}/jupyter-notebook.conf
    - source: salt://jupyter/templates/jupyter-notebook.conf
    - template: jinja
    - makedirs: true
    - require:
      - sls: supervisor

notebooks-dir:
  file.directory:
    - name: {{ notebooks_dir }}
    - user: {{ user }}
    - group: {{ user }}

notebook-update-supervisor:
  cmd.wait:
    - name: {{ supervisorctl }} -c {{ supervisord_conf }} update && sleep 2
    - watch:
      - file: jupyter-notebook.conf

notebook-running:
  supervisord.running:
    - name: jupyter-notebook
    - bin_env: {{ supervisorctl }}
    - conf_file: {{ supervisord_conf }}
    - require:
        - cmd: notebook-update-supervisor

notebook-restart-if-change:
  cmd.wait:
    - name: {{ supervisorctl }} -c {{ supervisord_conf }} restart jupyter-notebook
    - watch:
      - sls: jupyter
      - file: notebooks-dir
      - file: jupyter-notebook.conf
      - cmd: notebook-update-supervisor
