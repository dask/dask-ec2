
{% set user = salt['pillar.get']('cluster:username', 'ubuntu')  %}

{%- set home_dir = salt['user.info'](user).home %}
{%- set jupyter_config_dir = '/' ~ home_dir ~ '/.jupyter/' %}

{%- set port = 8888 %}
{%- set notebooks_dir = '/' ~ home_dir ~ '/notebooks' %}
