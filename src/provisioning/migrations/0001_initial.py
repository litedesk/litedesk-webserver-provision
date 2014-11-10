# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import jsonfield.fields
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
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
            },
            bases=('tenants.tenantservice',),
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
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
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
            bases=('tenants.tenantservice',),
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
            bases=('tenants.tenantservice',),
        ),
        migrations.CreateModel(
            name='Software',
            fields=[
                ('asset_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='provisioning.Asset')),
                ('web', models.BooleanField(default=True)),
                ('mobile', models.BooleanField(default=False)),
                ('desktop', models.BooleanField(default=False)),
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
            name='UserDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('start', models.DateTimeField(null=True, verbose_name='start', blank=True)),
                ('end', models.DateTimeField(null=True, verbose_name='end', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'staged', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'staged', b'staged'), (b'pending', b'pending'), (b'active', b'active'), (b'suspended', b'suspended'), (b'deprovisioned', b'deprovisioned')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('device', models.ForeignKey(to='provisioning.Device')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserMobileDataPlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('start', models.DateTimeField(null=True, verbose_name='start', blank=True)),
                ('end', models.DateTimeField(null=True, verbose_name='end', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'staged', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'staged', b'staged'), (b'pending', b'pending'), (b'active', b'active'), (b'suspended', b'suspended'), (b'deprovisioned', b'deprovisioned')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('mobile_data_plan', models.ForeignKey(to='provisioning.MobileDataPlan')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserPlatform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('start', models.DateTimeField(null=True, verbose_name='start', blank=True)),
                ('end', models.DateTimeField(null=True, verbose_name='end', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'staged', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'staged', b'staged'), (b'pending', b'pending'), (b'active', b'active'), (b'suspended', b'suspended'), (b'deprovisioned', b'deprovisioned')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('platform', models.ForeignKey(to='tenants.TenantService')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserSoftware',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('start', models.DateTimeField(null=True, verbose_name='start', blank=True)),
                ('end', models.DateTimeField(null=True, verbose_name='end', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'staged', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'staged', b'staged'), (b'pending', b'pending'), (b'active', b'active'), (b'suspended', b'suspended'), (b'deprovisioned', b'deprovisioned')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
                ('software', models.ForeignKey(to='provisioning.Software')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='tenantserviceasset',
            unique_together=set([('service', 'asset')]),
        ),
        migrations.AlterUniqueTogether(
            name='tenantasset',
            unique_together=set([('tenant', 'asset')]),
        ),
    ]
