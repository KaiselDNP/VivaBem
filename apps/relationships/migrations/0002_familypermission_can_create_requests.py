from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("relationships", "0001_initial")]
    operations = [migrations.AddField(
        model_name="familypermission",
        name="can_create_requests",
        field=models.BooleanField(default=False, verbose_name="criar pedidos de ajuda em meu nome"),
    )]
