# Documentation:
# http://www.cloudera.com/content/www/en-us/documentation/enterprise/latest/topics/cm_ig_install_path_b.html

include:
  - java
  - cloudera.repo

# https://github.com/saltstack/salt/issues/10852
noop:
  cmd.run:
    - name: echo 'noop' 
