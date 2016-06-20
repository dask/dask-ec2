{%- from 'java/openjdk/settings.sls' import java with context %}

include:
  - java.openjdk.env

java:
  pkg.installed:
    - name: {{ java.name }}
  alternatives.set:
    - name: java
    - path: {{java.bin_path}}/java
