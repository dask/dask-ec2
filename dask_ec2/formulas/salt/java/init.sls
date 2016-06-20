
include:
  - java.openjdk

# https://github.com/saltstack/salt/issues/10852
dummy:
  cmd.run:
    - name: echo 1
