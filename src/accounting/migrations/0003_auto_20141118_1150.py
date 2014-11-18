# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('accounting', '0002_contract_offer'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='tenant',
            field=models.ForeignKey(to='tenants.Tenant'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='charge',
            name='contract',
            field=models.ForeignKey(to='accounting.Contract'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='charge',
            name='tenant',
            field=models.ForeignKey(to='tenants.Tenant'),
            preserve_default=True,
        ),
    ]
