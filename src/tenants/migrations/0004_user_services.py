# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_auto_20141120_2049'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='services',
            field=models.ManyToManyField(to='tenants.TenantService'),
            preserve_default=True,
        ),
    ]
