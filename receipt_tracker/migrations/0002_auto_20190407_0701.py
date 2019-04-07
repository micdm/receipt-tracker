# Generated by Django 2.1.7 on 2019-04-07 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('receipt_tracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='addreceipttask',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='addreceipttask',
            name='buyer',
        ),
        migrations.AlterField(
            model_name='product',
            name='barcode',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='fiscal_document_number',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='fiscal_drive_number',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='receipt',
            name='fiscal_sign',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='seller',
            name='individual_number',
            field=models.CharField(max_length=15, unique=True),
        ),
        migrations.DeleteModel(
            name='AddReceiptTask',
        ),
    ]
