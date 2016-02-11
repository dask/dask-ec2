jdk-config:
  file.managed:
    - name: /etc/profile.d/java.sh
    - source: salt://java/openjdk/templates/java.sh
    - template: jinja
    - mode: 644
    - user: root
    - group: root
