from django.db import models
from django.contrib.auth.models import User
from math import floor

class Membre(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    profil = models.ImageField(upload_to='uploads/Membre', default='uploads/Membre/unknown_pdp.jpg')
    level = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    has_completed_initial_test = models.BooleanField(default=False)
    

    def update_level(self):
        if self.points < 100:
            new_level = 0
        else:
            new_level = max(0, floor((self.points - 100) / 300) + 1)
        
        # Check if level changed
        if new_level != self.level:
            old_level = self.level
            self.level = new_level
            self.save()
            return True, old_level, new_level
        return False, self.level, self.level

    def __str__(self):
        return f"{self.prenom} {self.nom} (Level {self.level})"


class InitialTest(models.Model):
    DIFFICULTY_CHOICES = [
        (1, 'Easy'),
        (2, 'Medium'),
        (3, 'Hard')
    ]
    
    question = models.TextField()
    test_cases = models.TextField()
    points = models.IntegerField(default=10)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)

    def __str__(self):
        return f"Question {self.id}"

    class Meta:
        ordering = ['difficulty', 'id']
