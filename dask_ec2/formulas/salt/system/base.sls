
git-pkg:
  pkg.installed:
    - pkgs:
      - git
      - graphviz

/etc/security/limits.conf:
  file.append:
    - source: salt://system/templates/limits.conf

python-pip:
  pkg.installed
