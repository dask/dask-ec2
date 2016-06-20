{% set version = salt['pillar.get']('java:version', '7') %}

{% set java = salt['grains.filter_by']({
    'Debian': {
        'name': 'openjdk-' ~ version ~ '-jre-headless',
        'bin_path': '/usr/lib/jvm/java-' ~ version ~ '-openjdk-amd64/jre/bin',
        'java_home': '/usr/lib/jvm/java-' ~ version  ~ '-openjdk-amd64/jre',
    },
    'RedHat': {
        'name': 'java-1.' ~ version ~ '.0-openjdk',
        'bin_path': '/usr/lib/jvm/jre-1.' ~ version ~ '.0-openjdk.x86_64/bin',
        'java_home': '/usr/lib/jvm/jre-1.' ~  version ~ '.0-openjdk.x86_64',
    },
}, merge=salt['pillar.get']('java:lookup')) %}
