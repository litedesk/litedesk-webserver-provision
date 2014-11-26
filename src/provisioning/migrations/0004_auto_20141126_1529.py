# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('provisioning', '0003_userprovisionhistory_service'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tenantprovisionable',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='tenantprovisionable',
            name='offer',
        ),
        migrations.RemoveField(
            model_name='tenantprovisionable',
            name='tenant',
        ),
        migrations.DeleteModel(
            name='TenantProvisionable',
        ),
        migrations.RemoveField(
            model_name='userprovisionhistory',
            name='offer',
        ),
    ]
