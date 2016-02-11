{% set install_prefix = salt['grains.get']('conda:install_prefix', salt['pillar.get']('conda:install_prefix', '/opt/anaconda/'))  %}
{% set download_url = 'https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh'  %}
