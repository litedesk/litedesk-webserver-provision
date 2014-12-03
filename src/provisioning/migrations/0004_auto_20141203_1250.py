# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0003_auto_20141203_1112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryentry',
            name='tenant_asset',
            field=models.ForeignKey(to='provisioning.TenantAsset'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inventoryentry',
            name='user',
            field=models.ForeignKey(to='tenants.User'),
            preserve_default=True,
        ),
    ]
