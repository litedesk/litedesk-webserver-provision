# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import provisioning.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('provisioning', '0001_initial'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='devices',
            field=provisioning.fields.ProvisionManyToManyField(to='provisioning.Device', through='provisioning.UserDevice'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='mobile_data_plans',
            field=provisioning.fields.ProvisionManyToManyField(to='provisioning.MobileDataPlan', through='provisioning.UserMobileDataPlan'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='platforms',
            field=provisioning.fields.ProvisionManyToManyField(to='tenants.TenantService', through='provisioning.UserPlatform'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='software',
            field=provisioning.fields.ProvisionManyToManyField(to='provisioning.Software', through='provisioning.UserSoftware'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='tenant',
            field=models.ForeignKey(to='tenants.Tenant'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together=set([('tenant', 'username')]),
        ),
        migrations.AddField(
            model_name='tenantservice',
            name='tenant',
            field=models.ForeignKey(to='tenants.Tenant'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tenantitem',
            name='content_type',
            field=models.ForeignKey(to='contenttypes.ContentType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tenantitem',
            name='tenant',
            field=models.ForeignKey(to='tenants.Tenant'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tenant',
            name='active_directory',
            field=models.OneToOneField(null=True, blank=True, to='tenants.ActiveDirectory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tenant',
            name='members',
            field=models.ManyToManyField(related_name='peers', to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tenant',
            name='primary_contact',
            field=models.OneToOneField(related_name='tenant', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
