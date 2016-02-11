#!py
import os
import logging

from salt.syspaths import BASE_PILLAR_ROOTS_DIR

log = logging.getLogger(__name__)


def run():
  """
  Returns all the pillars in the pillars directory
  """
  matches = []
  for pillar_tmp in os.listdir(BASE_PILLAR_ROOTS_DIR):
    pillar, ext = os.path.splitext(pillar_tmp)
    if ext != "" and ext != ".sls":
      log.debug("Pillar: Skipping bogus file: %s" % (pillar_tmp,))
      continue
    if is_available(BASE_PILLAR_ROOTS_DIR, pillar):
      matches.append(pillar)
  if matches == []:
    return {}
  else:
    return {'base': {'*': matches}}


def is_available(pillar_path, pillar_name):
  if pillar_name == "top":
    return False
  if pillar_name.startswith("."):
    return False

  log.debug("Checking pillar: %s" % (pillar_name,))
  if os.path.isfile(os.path.join(pillar_path, pillar_name + ".sls" )):
    return True
  if os.path.exists(os.path.join(pillar_path, pillar_name)):
    return True
  return False
