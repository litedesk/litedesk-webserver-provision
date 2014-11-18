# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import __builtin__
import model_utils.fields
import jsonfield.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Charge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', model_utils.fields.StatusField(default=b'scheduled', max_length=100, verbose_name='status', no_check_for_status=True, choices=[(b'scheduled', b'scheduled'), (b'waived', b'waived'), (b'pending', b'pending'), (b'paid', b'paid')])),
                ('status_changed', model_utils.fields.MonitorField(default=django.utils.timezone.now, verbose_name='status changed', monitor='status')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('active', models.BooleanField(default=True)),
                ('extra', jsonfield.fields.JSONField(default=__builtin__.dict)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
