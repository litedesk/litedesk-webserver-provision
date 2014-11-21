# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_auto_20141119_0138'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='devices',
        ),
        migrations.RemoveField(
            model_name='user',
            name='mobile_data_plans',
        ),
        migrations.RemoveField(
            model_name='user',
            name='platforms',
        ),
        migrations.RemoveField(
            model_name='user',
            name='software',
        ),
    ]
