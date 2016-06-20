{%- from 'java/settings.sls' import java with context %}

/tmp/java.debug:
    file.managed:
        - contents: |
            java_home: {{ java['java_home'] }}
