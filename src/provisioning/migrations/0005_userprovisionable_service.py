# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_user_services'),
        ('provisioning', '0004_auto_20141121_1419'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprovisionable',
            name='service',
            field=models.ForeignKey(default=1, to='tenants.TenantService'),
            preserve_default=False,
        ),
    ]
