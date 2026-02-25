from django.db import migrations, models

def migrate_existing_users(apps, schema_editor):
    """Marque les utilisateurs existants comme vérifiés mais nécessitant un MDP"""
    User = apps.get_model('base_api', 'User')
    
    # Tous les users existants avant cette migration sont considérés comme vérifiés
    # mais doivent définir un mot de passe
    User.objects.filter(
        is_phone_verified=False
    ).update(
        is_phone_verified=True,      # Déjà vérifié par l'ancien système OTP
        password_setup_required=True  # Doit définir un MDP
    )

class Migration(migrations.Migration):
    dependencies = [
        ('base_api', '0006_business_metadata_alter_business_business_type'),  # Adapte selon ta dernière migration
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_setup_required',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_phone_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrate_existing_users),
    ]