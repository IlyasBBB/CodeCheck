from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
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
            # Calculate level based on points
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


class ProblemCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Domain(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class")
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

    @classmethod
    def get_default_domain(cls):
        domain, _ = cls.objects.get_or_create(
            name='General',
            defaults={
                'description': 'General programming problems',
                'icon': 'fas fa-code'
            }
        )
        return domain.id


class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    domain = models.ForeignKey(
        Domain, 
        on_delete=models.CASCADE, 
        related_name='problems',
        default=Domain.get_default_domain
    )
    test_cases = models.TextField()  # JSON field for test cases
    solution_template = models.TextField(default="def solution():\n    pass")
    points = models.IntegerField(default=10)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    time_limit = models.IntegerField(default=300, help_text="Time limit in seconds")
    penalty_points = models.IntegerField(default=5, help_text="Points deducted if time limit exceeded")

    def __str__(self):
        return f"{self.title} ({self.difficulty})"

    class Meta:
        ordering = ['difficulty', 'created_at']


class Submission(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('S', 'Success'),
        ('F', 'Failed'),
        ('T', 'Time Limit Exceeded')
    ]

    user = models.ForeignKey(Membre, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    submission_time = models.DateTimeField(auto_now_add=True)
    execution_time = models.FloatField(null=True)

    def __str__(self):
        return f"{self.user} - {self.problem} ({self.get_status_display()})"


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


class TestResult(models.Model):
    user = models.ForeignKey(Membre, on_delete=models.CASCADE)
    test = models.ForeignKey(InitialTest, on_delete=models.CASCADE)
    answer = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    taken_at = models.DateTimeField(auto_now_add=True)