{%- macro get_nodes_for_role(role, module='get_hostname', index=none, separator=',', prefix='', suffix='') -%}
  {%- set force_mine_update = salt['mine.send']('network.' ~ module) -%}

  {%- set nodes = salt['mine.get']('roles:' ~ role, 'network.' ~ module, 'grain') -%}
  {%- set nodes_list = nodes.values() -%}

  {%- if nodes_list | length > 0 -%}

    {%- if prefix != '' or suffix != '' -%}
      {%- set nodes_list_copy = nodes_list -%}
      {%- set nodes_list = [] -%}
      {%- for node in nodes_list_copy -%}
        {%- do nodes_list.append(prefix ~ node ~ suffix) -%}
      {%- endfor -%}
    {%- endif -%}

    {%- if index is not none -%}
      {{ nodes_list[index] }}
    {%- else -%}
      {{ nodes_list | join(separator) }}
    {%- endif -%}
  {%- else -%}
      {{ 'localhost' | string() }}
  {%- endif -%}
{%- endmacro -%}
