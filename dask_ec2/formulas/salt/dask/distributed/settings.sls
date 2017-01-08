{%- from 'system/macros.sls' import get_nodes_for_role with context -%}

{%- set force_mine_update = salt['mine.send']('network.get_hostname') -%}
{%- set scheduler_host = get_nodes_for_role('dask.distributed.scheduler', index=0) -%}

{%- set scheduler_public_ip = salt['pillar.get']('dask:scheduler_public_ip', 1) -%}

{%- set numprocs = grains.get('num_cpus', 1) -%}

# My settings
{% set roles = grains['roles'] %}
{% set is_scheduler = 'dask.distributed.scheduler' in roles %}
{% set is_worker = 'dask.distributed.worker' in roles %}
{% set nprocs = salt['pillar.get']('dask:dask-worker:nprocs', 1)  %}
{% set source_install = salt['pillar.get']('dask:source_install', false)  %}
