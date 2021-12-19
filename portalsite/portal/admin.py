from django.contrib import admin
from . import models as dbm

# Register your models here.
admin.site.register(dbm.Label)
admin.site.register(dbm.Measurement)
admin.site.register(dbm.Model)
admin.site.register(dbm.Scoring)
admin.site.register(dbm.Source)
admin.site.register(dbm.Prediction)
