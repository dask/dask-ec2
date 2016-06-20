{% set install_prefix = salt['grains.get']('conda:install_prefix', salt['pillar.get']('conda:install_prefix', '/opt/anaconda/'))  %}

{%- if salt['pillar.get']('conda:pyversion', 3) == 2 %}
{% set download_url = 'https://repo.continuum.io/archive/Anaconda2-2.5.0-Linux-x86_64.sh'  %}
{%- else -%}
{% set download_url = 'https://repo.continuum.io/archive/Anaconda3-2.5.0-Linux-x86_64.sh'  %}
{%- endif -%}
