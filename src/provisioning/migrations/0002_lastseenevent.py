# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('contenttypes', '0001_initial'),
        ('provisioning', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LastSeenEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('object_id', models.PositiveIntegerField()),
                ('last_seen', models.DateTimeField()),
                ('item_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(to='tenants.User')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
