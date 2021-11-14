# Generated by Django 3.2.9 on 2021-11-14 14:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Measurement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('json_data', models.TextField(help_text='json object containing the measurement data')),
                ('notes', models.TextField(blank=True, help_text='description or notes for this measurement', null=True)),
                ('time_measured', models.DateTimeField(help_text='time the data was measured')),
                ('time_created', models.DateTimeField(auto_now_add=True, help_text='fist time this measurement was saved to database')),
                ('time_changed', models.DateTimeField(auto_now=True, help_text='last time this measurement was changed')),
            ],
            options={
                'ordering': ['time_created'],
            },
        ),
        migrations.CreateModel(
            name='MeasurementDataType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Model',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('data_type', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='portal.measurementdatatype')),
            ],
        ),
        migrations.CreateModel(
            name='ModelType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Scoring',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(default=0)),
                ('measurement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portal.measurement')),
                ('model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portal.model')),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.DeleteModel(
            name='MeasurementData',
        ),
        migrations.AddField(
            model_name='model',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='portal.modeltype'),
        ),
        migrations.AddField(
            model_name='measurement',
            name='data_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='portal.measurementdatatype'),
        ),
        migrations.AddField(
            model_name='measurement',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='portal.source'),
        ),
    ]
