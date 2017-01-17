{% set install_prefix = salt['grains.get']('conda:install_prefix', salt['pillar.get']('conda:install_prefix', '/opt/anaconda/'))  %}

{%- set py_version = salt['pillar.get']('conda:pyversion', 3) %}

{%- if py_version == 2 %}
{% set download_url = 'https://repo.continuum.io/archive/Anaconda2-4.2.0-Linux-x86_64.sh' %}
{% set download_hash = 'md5=a0d1fbe47014b71c6764d76fb403f217' %}

{%- else -%}
{% set download_url = 'https://repo.continuum.io/archive/Anaconda3-4.2.0-Linux-x86_64.sh' %}
{% set download_hash = 'md5=4692f716c82deb9fa6b59d78f9f6e85c' %}

{%- endif -%}
