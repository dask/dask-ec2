base:

  {% set states = salt['cp.list_states'](env) %}

  '*':
    {% if 'roles' in grains %}
    {% for role in grains['roles'] %}
    {% if role in states %}
    - {{ role }}
    {% endif %}  # state exists
    {% endfor %} # for roles
    {% endif %}  # role exists
