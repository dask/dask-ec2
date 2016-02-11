include:
  - cloudera.manager.base

server-packages:
  pkg.installed:
    - names:
      - cloudera-manager-daemons
      - cloudera-manager-server-db-2
      - cloudera-manager-server
    - require:
      - sls: cloudera.manager.base

server-db-services:
  service.running:
    - name: cloudera-scm-server-db
    - watch:
      - pkg: server-packages

server-services:
  service.running:
    - name: cloudera-scm-server
    - watch:
      - pkg: server-packages
      - service: server-db-services
