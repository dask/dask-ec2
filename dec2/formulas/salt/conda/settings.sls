{% set install_prefix = salt['grains.get']('conda:install_prefix', salt['pillar.get']('conda:install_prefix', '/opt/anaconda/'))  %}

{%- if salt['pillar.get']('conda:pyversion', 3) == 2 %}
{% set download_url = 'https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh'  %}
{%- else -%}
{% set download_url = 'https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh'  %}
{%- endif -%}
