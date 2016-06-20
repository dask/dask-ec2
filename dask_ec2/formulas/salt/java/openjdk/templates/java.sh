{%- from 'java/openjdk/settings.sls' import java with context %}

export JAVA_HOME={{ java.java_home }}
export JRE_HOME={{ java.java_home }}
export PATH=$JAVA_HOME/bin:$PATH
