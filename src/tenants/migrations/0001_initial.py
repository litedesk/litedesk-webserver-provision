# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveDirectory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=300)),
                ('domain', models.CharField(max_length=200)),
                ('ou', models.CharField(max_length=200)),
                ('username', models.CharField(max_length=80)),
                ('password', models.CharField(max_length=1000)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(unique=True, max_length=1000, db_index=True)),
                ('active', models.BooleanField(default=True)),
                ('email_domain', models.CharField(default=b'onmicrosoft.com', max_length=300)),
                ('active_directory', models.OneToOneField(null=True, blank=True, to='tenants.ActiveDirectory')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TenantItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('tenant', models.ForeignKey(to='tenants.Tenant')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TenantService',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True)),
                ('api_token', models.CharField(max_length=128)),
                ('tenant', models.ForeignKey(to='tenants.Tenant')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('last_remote_read', models.DateTimeField(null=True, editable=False)),
                ('last_remote_save', models.DateTimeField(null=True, editable=False)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=100, null=True)),
                ('last_name', models.CharField(max_length=100, null=True)),
                ('display_name', models.CharField(max_length=200, null=True)),
                ('mobile_phone_number', models.CharField(max_length=16, null=True, blank=True)),
                ('username', models.CharField(max_length=100, editable=False)),
                ('email', models.EmailField(max_length=75, null=True)),
                ('status', model_utils.fields.StatusField(default=b'staged', max_length=100, no_check_for_status=True, choices=[(b'staged', b'staged'), (b'pending', b'pending'), (b'active', b'active'), (b'suspended', b'suspended'), (b'disabled', b'disabled')])),
                ('services', models.ManyToManyField(to='tenants.TenantService')),
                ('tenant', models.ForeignKey(to='tenants.Tenant')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=80)),
                ('members', models.ManyToManyField(to='tenants.User', blank=True)),
                ('tenant', models.ForeignKey(to='tenants.Tenant')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='usergroup',
            unique_together=set([('name', 'tenant')]),
        ),
        migrations.AlterUniqueTogether(
            name='user',
            unique_together=set([('tenant', 'username')]),
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
