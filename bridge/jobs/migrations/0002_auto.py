# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-27 12:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='weight',
            field=models.CharField(choices=[('0', 'Full-weight'), ('1', 'Medium-weight'), ('2', 'Lightweight')], default='0', max_length=1),
        ),
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(choices=[('0', 'Not solved'), ('1', 'Pending'), ('2', 'Is solving'), ('3', 'Solved'), ('4', 'Failed'), ('5', 'Corrupted'), ('6', 'Cancelled'), ('7', 'Terminated')], default='0', max_length=1),
        ),
        migrations.AlterField(
            model_name='runhistory',
            name='status',
            field=models.CharField(choices=[('0', 'Not solved'), ('1', 'Pending'), ('2', 'Is solving'), ('3', 'Solved'), ('4', 'Failed'), ('5', 'Corrupted'), ('6', 'Cancelled'), ('7', 'Terminated')], default='1', max_length=1),
        ),
    ]