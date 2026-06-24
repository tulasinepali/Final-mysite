import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import sys

project_home = "/home/tulasine/learning-platformfinal"

if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "learning_platform.settings"
)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()