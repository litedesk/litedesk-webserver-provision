# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('provisioning', '0002_auto_20141125_1734'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprovisionhistory',
            name='service',
            field=models.ForeignKey(default=1, to='tenants.TenantService'),
            preserve_default=False,
        ),
    ]
