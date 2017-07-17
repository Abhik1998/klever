# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-07-14 09:32
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('marks', '0013_auto_20170516_1157'),
    ]

    operations = [
        migrations.CreateModel(
            name='SafeTagAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modification', models.BooleanField(default=False)),
                ('child_creation', models.BooleanField(default=False)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marks.SafeTag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UnsafeTagAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modification', models.BooleanField(default=False)),
                ('child_creation', models.BooleanField(default=False)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marks.UnsafeTag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]