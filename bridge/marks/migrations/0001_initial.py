# Generated by Django 2.1.3 on 2019-03-21 12:14

import bridge.utils
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ConvertedTrace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash_sum', models.CharField(db_index=True, max_length=255)),
                ('file', models.FileField(upload_to='Error-traces')),
                ('function', models.CharField(db_index=True, max_length=30)),
                ('trace_cache', django.contrib.postgres.fields.jsonb.JSONField()),
            ],
            options={
                'db_table': 'cache_marks_trace',
            },
            bases=(bridge.utils.WithFilesMixin, models.Model),
        ),
        migrations.CreateModel(
            name='MarkSafe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('format', models.PositiveSmallIntegerField(default=1)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('is_modifiable', models.BooleanField(default=True)),
                ('type', models.CharField(choices=[('0', 'Created'), ('1', 'Preset'), ('2', 'Uploaded')], default='0', max_length=1)),
                ('cache_attrs', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('verdict', models.CharField(choices=[('0', 'Unknown'), ('1', 'Incorrect proof'), ('2', 'Missed target bug')], max_length=1)),
                ('cache_tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), default=list, size=None)),
            ],
            options={
                'db_table': 'mark_safe',
            },
        ),
        migrations.CreateModel(
            name='MarkSafeAttr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=64, unique=True)),
                ('value', models.CharField(max_length=255)),
                ('is_compare', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'mark_safe_attr',
            },
        ),
        migrations.CreateModel(
            name='MarkSafeHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('0', 'Unreported'), ('1', 'Reported'), ('2', 'Fixed'), ('3', 'Rejected')], default='0', max_length=1)),
                ('change_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('comment', models.TextField(blank=True, default='')),
                ('description', models.TextField(blank=True, default='')),
                ('verdict', models.CharField(choices=[('0', 'Unknown'), ('1', 'Incorrect proof'), ('2', 'Missed target bug')], max_length=1)),
            ],
            options={
                'db_table': 'mark_safe_history',
            },
        ),
        migrations.CreateModel(
            name='MarkSafeReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('0', 'Automatic'), ('1', 'Confirmed'), ('2', 'Unconfirmed')], default='0', max_length=1)),
            ],
            options={
                'db_table': 'cache_mark_safe_report',
            },
        ),
        migrations.CreateModel(
            name='MarkSafeTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'cache_mark_safe_tag',
            },
        ),
        migrations.CreateModel(
            name='MarkUnknown',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('format', models.PositiveSmallIntegerField(default=1)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('is_modifiable', models.BooleanField(default=True)),
                ('type', models.CharField(choices=[('0', 'Created'), ('1', 'Preset'), ('2', 'Uploaded')], default='0', max_length=1)),
                ('cache_attrs', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('component', models.CharField(max_length=20)),
                ('function', models.TextField()),
                ('is_regexp', models.BooleanField(default=True)),
                ('problem_pattern', models.CharField(max_length=20)),
                ('link', models.URLField(null=True)),
            ],
            options={
                'db_table': 'mark_unknown',
            },
        ),
        migrations.CreateModel(
            name='MarkUnknownAttr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=64, unique=True)),
                ('value', models.CharField(max_length=255)),
                ('is_compare', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'mark_unknown_attr',
            },
        ),
        migrations.CreateModel(
            name='MarkUnknownHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('0', 'Unreported'), ('1', 'Reported'), ('2', 'Fixed'), ('3', 'Rejected')], default='0', max_length=1)),
                ('change_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('comment', models.TextField(blank=True, default='')),
                ('description', models.TextField(blank=True, default='')),
                ('function', models.TextField()),
                ('is_regexp', models.BooleanField(default=True)),
                ('problem_pattern', models.CharField(max_length=20)),
                ('link', models.URLField(null=True)),
            ],
            options={
                'db_table': 'mark_unknown_history',
            },
        ),
        migrations.CreateModel(
            name='MarkUnknownReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('problem', models.CharField(db_index=True, max_length=20)),
                ('type', models.CharField(choices=[('0', 'Automatic'), ('1', 'Confirmed'), ('2', 'Unconfirmed')], default='0', max_length=1)),
            ],
            options={
                'db_table': 'cache_mark_unknown_report',
            },
        ),
        migrations.CreateModel(
            name='MarkUnsafe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('format', models.PositiveSmallIntegerField(default=1)),
                ('version', models.PositiveSmallIntegerField(default=1)),
                ('is_modifiable', models.BooleanField(default=True)),
                ('type', models.CharField(choices=[('0', 'Created'), ('1', 'Preset'), ('2', 'Uploaded')], default='0', max_length=1)),
                ('cache_attrs', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('function', models.CharField(db_index=True, max_length=30)),
                ('verdict', models.CharField(choices=[('0', 'Unknown'), ('1', 'Bug'), ('2', 'Target bug'), ('3', 'False positive')], max_length=1)),
                ('cache_tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=32), default=list, size=None)),
            ],
            options={
                'db_table': 'mark_unsafe',
            },
        ),
        migrations.CreateModel(
            name='MarkUnsafeAttr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=64, unique=True)),
                ('value', models.CharField(max_length=255)),
                ('is_compare', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'mark_unsafe_attr',
            },
        ),
        migrations.CreateModel(
            name='MarkUnsafeHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveSmallIntegerField()),
                ('status', models.CharField(choices=[('0', 'Unreported'), ('1', 'Reported'), ('2', 'Fixed'), ('3', 'Rejected')], default='0', max_length=1)),
                ('change_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('comment', models.TextField(blank=True, default='')),
                ('description', models.TextField(blank=True, default='')),
                ('function', models.CharField(db_index=True, max_length=30)),
                ('verdict', models.CharField(choices=[('0', 'Unknown'), ('1', 'Bug'), ('2', 'Target bug'), ('3', 'False positive')], max_length=1)),
            ],
            options={
                'db_table': 'mark_unsafe_history',
            },
        ),
        migrations.CreateModel(
            name='MarkUnsafeReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('0', 'Automatic'), ('1', 'Confirmed'), ('2', 'Unconfirmed')], default='0', max_length=1)),
                ('result', models.FloatField()),
                ('error', models.TextField(null=True)),
            ],
            options={
                'db_table': 'cache_mark_unsafe_report',
            },
        ),
        migrations.CreateModel(
            name='MarkUnsafeTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'cache_mark_unsafe_tag',
            },
        ),
        migrations.CreateModel(
            name='SafeAssociationLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dislike', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'mark_safe_association_like',
            },
        ),
        migrations.CreateModel(
            name='SafeTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=32)),
                ('description', models.TextField(default='')),
                ('populated', models.BooleanField(default=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
                'db_table': 'mark_safe_tag',
            },
        ),
        migrations.CreateModel(
            name='SafeTagAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modification', models.BooleanField(default=False)),
                ('child_creation', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'marks_safe_tag_access',
            },
        ),
        migrations.CreateModel(
            name='UnknownAssociationLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dislike', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'mark_unknown_association_like',
            },
        ),
        migrations.CreateModel(
            name='UnsafeAssociationLike',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dislike', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'mark_unsafe_association_like',
            },
        ),
        migrations.CreateModel(
            name='UnsafeConvertionCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'cache_error_trace_converted',
            },
        ),
        migrations.CreateModel(
            name='UnsafeTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=32)),
                ('description', models.TextField(default='')),
                ('populated', models.BooleanField(default=False)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
            ],
            options={
                'db_table': 'mark_unsafe_tag',
            },
        ),
        migrations.CreateModel(
            name='UnsafeTagAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modification', models.BooleanField(default=False)),
                ('child_creation', models.BooleanField(default=False)),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marks.UnsafeTag')),
            ],
            options={
                'db_table': 'marks_unsafe_tag_access',
            },
        ),
    ]
