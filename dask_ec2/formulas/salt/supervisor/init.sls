
supervisor-pkg:
    pkg.installed:
        - name: supervisor

supervisor:
  service.running:
    - enable: True
