
git-pkg:
  pkg.installed:
    - name: git

/etc/security/limits.conf:
  file.append:
    - source: salt://system/templates/limits.conf
