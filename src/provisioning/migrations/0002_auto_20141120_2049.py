# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_auto_20141120_2049'),
        ('catalog', '0001_initial'),
        ('provisioning', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProvisionable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('offer', models.ForeignKey(to='catalog.Offer')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='userdevice',
            name='device',
        ),
        migrations.RemoveField(
            model_name='userdevice',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserDevice',
        ),
        migrations.RemoveField(
            model_name='usermobiledataplan',
            name='mobile_data_plan',
        ),
        migrations.RemoveField(
            model_name='usermobiledataplan',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserMobileDataPlan',
        ),
        migrations.RemoveField(
            model_name='userplatform',
            name='platform',
        ),
        migrations.RemoveField(
            model_name='userplatform',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserPlatform',
        ),
        migrations.RemoveField(
            model_name='usersoftware',
            name='software',
        ),
        migrations.RemoveField(
            model_name='usersoftware',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserSoftware',
        ),
        migrations.RemoveField(
            model_name='software',
            name='desktop',
        ),
        migrations.RemoveField(
            model_name='software',
            name='mobile',
        ),
        migrations.RemoveField(
            model_name='software',
            name='web',
        ),
        migrations.AddField(
            model_name='asset',
            name='desktop',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='asset',
            name='mobile',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='asset',
            name='web',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
