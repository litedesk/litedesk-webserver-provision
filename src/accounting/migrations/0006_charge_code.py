# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0005_auto_20141118_2359'),
    ]

    operations = [
        migrations.AddField(
            model_name='charge',
            name='code',
            field=models.CharField(default=1, max_length=30),
            preserve_default=False,
        ),
    ]
