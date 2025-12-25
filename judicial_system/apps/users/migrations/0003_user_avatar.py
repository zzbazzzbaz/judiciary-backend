from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_performancehistory"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="users/avatars/%Y/%m/",
                verbose_name="头像",
            ),
        ),
    ]
