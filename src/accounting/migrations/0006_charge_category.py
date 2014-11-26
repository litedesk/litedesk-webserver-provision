# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0005_auto_20141126_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='charge',
            name='category',
            field=models.CharField(default='software', max_length=50, choices=[(b'platform', b'platform'), (b'software', b'software'), (b'devices', b'devices')]),
            preserve_default=False,
        ),
    ]
