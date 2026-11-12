from config.env import csv

from .base import *
from .environment import *

DEBUG = False
ALLOWED_HOSTS = csv("ALLOWED_HOSTS")
