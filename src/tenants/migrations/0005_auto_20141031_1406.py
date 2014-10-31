# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_auto_20141028_1355'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_synced_at',
        ),
        migrations.AddField(
            model_name='user',
            name='last_remote_read',
            field=models.DateTimeField(null=True, editable=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='last_remote_save',
            field=models.DateTimeField(null=True, editable=False),
            preserve_default=True,
        ),
    ]
