# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import provisioning.models
import autoslug.fields
import jsonfield.fields
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('tenants', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AirWatch',
            fields=[
                ('tenantservice_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='tenants.TenantService')),
                ('username', models.CharField(max_length=80)),
                ('password', models.CharField(max_length=1000)),
                ('server_url', models.URLField()),
                ('group_id', models.CharField(max_length=80)),
            ],
            options={
                'verbose_name': 'AirWatch',
            },
            bases=('tenants.tenantservice', provisioning.models.Provisionable),
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=1000)),
                ('slug', autoslug.fields.AutoSlugField(default=b'', editable=False)),
                ('description', models.TextField(null=True, blank=True)),
                ('web', models.BooleanField(default=True)),
                ('mobile', models.BooleanField(default=False)),
                ('desktop', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, provisioning.models.Provisionable),
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='provisioning.Asset')),
                ('image', models.ImageField(null=True, upload_to=b'', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('provisioning.asset',),
        ),
        migrations.CreateModel(
            name='MobileDataPlan',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='provisioning.Asset')),
            ],
            options={
                'abstract': False,
            },
            bases=('provisioning.asset',),
        ),
        migrations.CreateModel(
            name='MobileIron',
            fields=[
                ('tenantservice_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='tenants.TenantService')),
            ],
            options={
            },
            bases=('tenants.tenantservice', provisioning.models.Provisionable),
        ),
        migrations.CreateModel(
            name='Okta',
            fields=[
                ('tenantservice_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='tenants.TenantService')),
                ('domain', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Okta',
            },
            bases=('tenants.tenantservice', provisioning.models.Provisionable),
        ),
        migrations.CreateModel(
            name='Software',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='provisioning.Asset')),
            ],
            options={
                'abstract': False,
            },
            bases=('provisioning.asset',),
        ),
        migrations.CreateModel(
            name='TenantAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metadata', jsonfield.fields.JSONField(null=True)),
                ('asset', models.ForeignKey(to='provisioning.Asset')),
                ('tenant', models.ForeignKey(to='tenants.Tenant')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
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
        migrations.CreateModel(
            name='TenantServiceAsset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('metadata', jsonfield.fields.JSONField(null=True)),
                ('asset', models.ForeignKey(to='provisioning.Asset')),
                ('service', models.ForeignKey(to='tenants.TenantService')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserProvisionable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', model_utils.fields.StatusField(default=b'staged', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'staged', b'staged'), (b'processing', b'processing'), (b'active', b'active')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('object_id', models.PositiveIntegerField()),
                ('item_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('service', models.ForeignKey(to='tenants.TenantService')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='userprovisionable',
            unique_together=set([('user', 'service', 'item_type', 'object_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='tenantserviceasset',
            unique_together=set([('service', 'asset')]),
        ),
        migrations.AlterUniqueTogether(
            name='tenantasset',
            unique_together=set([('tenant', 'asset')]),
        ),
        migrations.CreateModel(
            name='ChromeDevice',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('provisioning.device',),
        ),
    ]
