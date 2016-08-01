{% set install_prefix = salt['grains.get']('conda:install_prefix', salt['pillar.get']('conda:install_prefix', '/opt/anaconda/'))  %}

{%- if salt['pillar.get']('conda:pyversion', 3) == 2 %}
{% set download_url = 'https://repo.continuum.io/archive/Anaconda2-2.5.0-Linux-x86_64.sh' %}
{% set download_hash = 'md5=f8eb687af8c9b4e81968de8c63b0d991' %}
{%- else -%}
{% set download_url = 'https://repo.continuum.io/archive/Anaconda3-2.5.0-Linux-x86_64.sh' %}
{% set download_hash = 'md5=02bac549e486be7096070db8d50d0c7f' %}
{%- endif -%}
