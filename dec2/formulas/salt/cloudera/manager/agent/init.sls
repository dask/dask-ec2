include:
  - cloudera.manager.base

agent-packages:
  pkg.installed:
    - names:
      - cloudera-manager-daemons
      - cloudera-manager-agent
    - require:
      - sls: cloudera.manager.base

/etc/cloudera-scm-agent/config.ini:
  file.managed:
    - source: salt://cloudera/etc/cloudera-scm-agent/config.ini
    - template: jinja
    - require:
      - pkg: agent-packages

agent-services:
  service.running:
    - name: cloudera-scm-agent
    - watch:
      - pkg: agent-packages
      - file: /etc/cloudera-scm-agent/config.ini
