# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0003_auto_20141127_1450'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='charge',
            name='category',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='end',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='extra',
        ),
        migrations.RemoveField(
            model_name='contract',
            name='start',
        ),
        migrations.AddField(
            model_name='contract',
            name='category',
            field=models.CharField(default=b'other', max_length=50, choices=[(b'platform', b'platform'), (b'software', b'software'), (b'devices', b'devices'), (b'other', b'other')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='contract',
            name='end_date',
            field=models.DateField(default=datetime.datetime(2014, 11, 27, 17, 10, 21, 413172)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='contract',
            name='start_date',
            field=models.DateField(default=datetime.datetime(2014, 11, 27, 17, 10, 26, 972617)),
            preserve_default=False,
        ),
    ]
