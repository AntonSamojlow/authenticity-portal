# Generated by Django 3.2.9 on 2021-11-26 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='measurement',
            name='name',
            field=models.CharField(default='measurement-540745b1-eaff-41bd-a7de-c867858fe2f9', max_length=50, unique=True),
        ),
    ]
