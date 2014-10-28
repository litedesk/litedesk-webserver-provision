# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_auto_20141024_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=model_utils.fields.StatusField(default=b'staged', max_length=100, no_check_for_status=True, choices=[(b'staged', b'staged'), (b'pending', b'pending'), (b'active', b'active'), (b'suspended', b'suspended'), (b'disabled', b'disabled')]),
        ),
    ]
