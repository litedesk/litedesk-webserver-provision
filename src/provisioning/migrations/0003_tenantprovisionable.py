# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_auto_20141120_2049'),
        ('catalog', '0001_initial'),
        ('provisioning', '0002_auto_20141120_2049'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantProvisionable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metadata', jsonfield.fields.JSONField(null=True)),
                ('offer', models.ForeignKey(to='catalog.Offer')),
                ('tenant', models.ForeignKey(to='tenants.Tenant')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
