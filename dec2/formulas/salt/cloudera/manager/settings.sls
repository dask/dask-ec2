{%- from 'system/macros.sls' import get_nodes_for_role with context %}

{%- set force_mine_update = salt['mine.send']('network.get_hostname') -%}
{%- set manager_host = get_nodes_for_role('cloudera.manager.server', index=0) -%}
