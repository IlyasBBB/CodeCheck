from django.core.management.base import BaseCommand
from Coding.models import Domain, Problem
import json

class Command(BaseCommand):
    help = 'Creates sample domains and problems'

    def handle(self, *args, **kwargs):
        # Create Domains
        domains_data = [
            {
                'name': 'Basic Programming',
                'description': 'Fundamental programming concepts and simple algorithms',
                'icon': 'fas fa-code'
            },
            {
                'name': 'Data Structures',
                'description': 'Arrays, Lists, Trees, and other data structures',
                'icon': 'fas fa-project-diagram'
            },
            {
                'name': 'Algorithms',
                'description': 'Sorting, Searching, and other algorithmic problems',
                'icon': 'fas fa-microchip'
            },
            {
                'name': 'String Manipulation',
                'description': 'Problems involving string operations and patterns',
                'icon': 'fas fa-font'
            },
            {
                'name': 'Mathematics',
                'description': 'Mathematical problems and number theory',
                'icon': 'fas fa-square-root-alt'
            }
        ]

        # Create domains
        domains = {}
        for i, domain_data in enumerate(domains_data):
            domain, created = Domain.objects.get_or_create(
                name=domain_data['name'],
                defaults={
                    'description': domain_data['description'],
                    'icon': domain_data['icon'],
                    'order': i
                }
            )
            domains[domain_data['name']] = domain

        # Problems data
        problems_data = [
            # Basic Programming
            {
                'domain': 'Basic Programming',
                'title': 'Sum of Two Numbers',
                'description': 'Write a function that returns the sum of two numbers.',
                'difficulty': 'easy',
                'points': 10,
                'test_cases': json.dumps([
                    {'input': '2, 3', 'expected': '5'},
                    {'input': '-1, 1', 'expected': '0'}
                ])
            },
            {
                'domain': 'Basic Programming',
                'title': 'Even or Odd',
                'description': 'Determine if a number is even or odd.',
                'difficulty': 'easy',
                'points': 10,
                'test_cases': json.dumps([
                    {'input': '4', 'expected': 'even'},
                    {'input': '7', 'expected': 'odd'}
                ])
            },
            # Data Structures
            {
                'domain': 'Data Structures',
                'title': 'Reverse Array',
                'description': 'Write a function to reverse an array.',
                'difficulty': 'easy',
                'points': 15,
                'test_cases': json.dumps([
                    {'input': '[1,2,3]', 'expected': '[3,2,1]'},
                    {'input': '[5,4]', 'expected': '[4,5]'}
                ])
            },
            # Continue with more problems...
            {
                'domain': 'Algorithms',
                'title': 'Binary Search',
                'description': 'Implement binary search algorithm.',
                'difficulty': 'medium',
                'points': 25,
                'test_cases': json.dumps([
                    {'input': '[1,2,3,4,5], 3', 'expected': '2'},
                    {'input': '[1,3,5,7], 7', 'expected': '3'}
                ])
            },
            # Add more problems here...
        ]

        # Create 30 problems
        for i in range(30):
            problem_data = problems_data[i % len(problems_data)]  # Cycle through sample problems
            modified_title = f"{problem_data['title']} {i+1}"  # Make titles unique
            
            Problem.objects.get_or_create(
                title=modified_title,
                defaults={
                    'domain': domains[problem_data['domain']],
                    'description': problem_data['description'],
                    'difficulty': problem_data['difficulty'],
                    'points': problem_data['points'],
                    'test_cases': problem_data['test_cases'],
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample data')) 