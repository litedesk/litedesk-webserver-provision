# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0002_lastseenevent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sku',
            name='device',
        ),
        migrations.RemoveField(
            model_name='sku',
            name='tenant',
        ),
        migrations.RemoveField(
            model_name='inventoryentry',
            name='sku',
        ),
        migrations.DeleteModel(
            name='SKU',
        ),
        migrations.AddField(
            model_name='inventoryentry',
            name='serial_number',
            field=models.CharField(default=b'N/A', max_length=100),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='inventoryentry',
            name='tenant_asset',
            field=models.ForeignKey(to='provisioning.TenantAsset', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inventoryentry',
            name='user',
            field=models.ForeignKey(to='tenants.User', null=True),
            preserve_default=True,
        ),
    ]
