{% set is_server = 'cloudera.manager.server' in grains['roles'] %}
{% set is_agent = 'cloudera.manager.agent' in grains['roles'] %}

{% if is_server or is_agent %}
include:
  {% if is_server %}
  - cloudera.manager.server
  - cloudera.manager.agent
  {% endif %}

  {% if is_agent %}
  - cloudera.manager.agent
  {% endif %}
{% endif %}
