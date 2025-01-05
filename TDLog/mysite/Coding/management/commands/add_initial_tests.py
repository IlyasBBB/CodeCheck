from django.core.management.base import BaseCommand
from Coding.models import InitialTest

class Command(BaseCommand):
    help = 'Add initial tests to the database'

    def handle(self, *args, **kwargs):
        tests = [
            {
                'question': 'What is the output of 2 + 2?',
                'test_cases': '2 + 2 == 4',
                'points': 10,
                'difficulty': 1
            },
            {
                'question': 'Explain the concept of OOP.',
                'test_cases': 'N/A',
                'points': 15,
                'difficulty': 2
            },
            {
                'question': 'What is the time complexity of binary search?',
                'test_cases': 'N/A',
                'points': 20,
                'difficulty': 3
            },
        ]
        for test in tests:
            InitialTest.objects.create(**test)
        self.stdout.write(self.style.SUCCESS('Initial tests added successfully.'))
