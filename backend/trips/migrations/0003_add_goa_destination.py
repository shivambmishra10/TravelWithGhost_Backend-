from django.db import migrations
from django.core.files import File
import os
import shutil

def add_goa_destination(apps, schema_editor):
    City = apps.get_model('trips', 'City')
    
    # Check if Goa already exists
    if not City.objects.filter(name='Goa').exists():
        # Create Goa city
        city = City(name='Goa')
        city.save()
        
        # Copy the Goa image to media directory if it doesn't exist
        source_image = os.path.join('media', 'Goa.jpg')
        if os.path.exists(source_image):
            # Create the destination directory if it doesn't exist
            os.makedirs('media', exist_ok=True)
            # Save the image to the city model
            with open(source_image, 'rb') as img_file:
                city.image.save('Goa.jpg', File(img_file), save=True)

def remove_goa_destination(apps, schema_editor):
    City = apps.get_model('trips', 'City')
    City.objects.filter(name='Goa').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('trips', '0002_alter_city_image'),
    ]

    operations = [
        migrations.RunPython(add_goa_destination, remove_goa_destination),
    ]