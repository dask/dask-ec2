{%- from 'conda/settings.sls' import install_prefix with context -%}

{% set password = salt['pillar.get']('jupyter:password', 'jupyter')  %}
{%- set hash_password = salt["cmd.run"](install_prefix ~ "/bin/python -c 'from notebook.auth import passwd; print(passwd(\"" ~ password ~ "\"))'") -%}
