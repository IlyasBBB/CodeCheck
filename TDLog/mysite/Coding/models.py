from django.db import models
from django.contrib.auth.models import User


class Membre(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    profil = models.ImageField(upload_to='uploads/Membre', default='uploads/Membre/unknown_pdp.jpg')

    def __str__(self):
        return f"{self.prenom} {self.nom}"