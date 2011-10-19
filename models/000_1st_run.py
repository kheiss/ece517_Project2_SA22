# -*- coding: utf-8 -*-
"""
    1st RUN:

    - Import the S3 Framework Extensions
    - If needed, copy deployment specific templates to the live installation.
      Developers: note that the templates are version-controlled, while their
                  site-specific copies are not (to avoid leaking of sensitive
                  or irrelevant information into the repository).
                  If you add something new to these files, you should also
                  make the change at deployment-templates and commit it.
"""
import os
from gluon import current
from gluon.storage import Storage
from gluon.contrib.simplejson.ordered_dict import OrderedDict

current.cache = cache

# Import the S3 Framework
import s3 as s3base
# Per-request values, e.g. for views, can be stored here to avoid conflict
# with web2py data.
response.s3 = Storage()
response.s3.gis = Storage()  # Defined early for use by S3Config.

deployment_settings = s3base.S3Config()
current.deployment_settings = deployment_settings

template_src = os.path.join("applications", request.application, "deployment-templates")
template_dst = os.path.join("applications", request.application)

template_files = (
    "models/000_config.py",
    "cron/crontab"
)

copied_from_template = []

for t in template_files:
    dst_path = os.path.join(template_dst, t)
    try:
        os.stat(dst_path)
    except OSError:
        # not found, copy from template
        import shutil
        shutil.copy(os.path.join(template_src, t), dst_path)
        copied_from_template.append(t)

if copied_from_template:
    raise HTTP(501, body="The following files were copied from templates and should be edited: %s" %
                         ", ".join(copied_from_template))

