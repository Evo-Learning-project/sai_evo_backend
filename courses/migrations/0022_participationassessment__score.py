# Generated by Django 4.0.1 on 2022-02-15 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0021_alter_eventtemplaterule_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='participationassessment',
            name='_score',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]