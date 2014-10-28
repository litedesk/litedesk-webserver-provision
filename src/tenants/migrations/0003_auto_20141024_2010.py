# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_auto_20141022_1754'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=model_utils.fields.StatusField(default=b'active', max_length=100, no_check_for_status=True, choices=[(b'active', b'active'), (b'suspended', b'suspended'), (b'deactivated', b'deactivated')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=100, editable=False),
        ),
    ]
