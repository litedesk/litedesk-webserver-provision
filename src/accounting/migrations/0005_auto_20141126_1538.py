# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0004_auto_20141126_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='charge',
            name='end_date',
            field=models.DateField(default=datetime.datetime(2014, 11, 26, 15, 38, 0, 260356)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='charge',
            name='start_date',
            field=models.DateField(default=datetime.datetime(2014, 11, 26, 15, 38, 12, 144408)),
            preserve_default=False,
        ),
    ]
