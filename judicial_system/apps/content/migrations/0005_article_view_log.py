from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_documentcategory_document_category'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleViewLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now_add=True, verbose_name='查看时间')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='view_logs', to='content.article', verbose_name='文章')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='article_view_logs', to=settings.AUTH_USER_MODEL, verbose_name='人员')),
            ],
            options={
                'verbose_name': '学习日志',
                'verbose_name_plural': '学习日志',
                'db_table': 'content_article_view_log',
            },
        ),
    ]
