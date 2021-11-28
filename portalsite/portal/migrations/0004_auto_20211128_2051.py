# Generated by Django 3.2.9 on 2021-11-28 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0003_alter_measurement_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='model',
            name='data',
            field=models.TextField(default="", help_text='model data (weights, parameters, coefficients, etc.), serialized to string'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='model',
            name='model_type',
            field=models.CharField(choices=[('Test', 'TestModelType'), ('LReg-2', '2-feature linear regression'), ('LReg-5', '5-feature linear regression')], max_length=10),
        ),
    ]
