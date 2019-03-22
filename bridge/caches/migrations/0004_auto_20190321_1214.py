# Generated by Django 2.1.3 on 2019-03-21 12:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('jobs', '0001_initial'),
        ('caches', '0003_unsafemarkassociationchanges_mark'),
        ('marks', '0001_initial'),
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='unsafemarkassociationchanges',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.ReportUnsafe'),
        ),
        migrations.AddField(
            model_name='unknownmarkassociationchanges',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobs.Job'),
        ),
        migrations.AddField(
            model_name='unknownmarkassociationchanges',
            name='mark',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marks.MarkUnknown'),
        ),
        migrations.AddField(
            model_name='unknownmarkassociationchanges',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.ReportUnknown'),
        ),
        migrations.AddField(
            model_name='testtablewithref',
            name='test',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='caches.TestTable'),
        ),
        migrations.AddField(
            model_name='safemarkassociationchanges',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobs.Job'),
        ),
        migrations.AddField(
            model_name='safemarkassociationchanges',
            name='mark',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marks.MarkSafe'),
        ),
        migrations.AddField(
            model_name='safemarkassociationchanges',
            name='report',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.ReportSafe'),
        ),
        migrations.AddField(
            model_name='reportunsafecache',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='jobs.Job'),
        ),
        migrations.AddField(
            model_name='reportunsafecache',
            name='report',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cache', to='reports.ReportUnsafe'),
        ),
        migrations.AddField(
            model_name='reportunknowncache',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='jobs.Job'),
        ),
        migrations.AddField(
            model_name='reportunknowncache',
            name='report',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cache', to='reports.ReportUnknown'),
        ),
        migrations.AddField(
            model_name='reportsafecache',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='jobs.Job'),
        ),
        migrations.AddField(
            model_name='reportsafecache',
            name='report',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cache', to='reports.ReportSafe'),
        ),
    ]
