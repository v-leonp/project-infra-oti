from django.db import migrations


def setup_roles(apps, schema_editor):
    from apps.administration.role_setup import setup_roles_and_permissions

    setup_roles_and_permissions()


class Migration(migrations.Migration):
    dependencies = [
        ("administration", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(setup_roles, migrations.RunPython.noop),
    ]
