from django.contrib import admin

from django.contrib import admin
from .models import InitialTest, Membre, Domain, Problem
import json

@admin.register(InitialTest)
class InitialTestAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'points', 'get_difficulty_display')
    list_filter = ('points',)
    search_fields = ('question',)

    def get_difficulty_display(self, obj):
        return obj.get_difficulty_display()
    get_difficulty_display.short_description = 'Difficulty'

    def save_model(self, request, obj, form, change):
        # Ensure test cases are properly formatted
        if isinstance(obj.test_cases, str):
            try:
                # Try to parse as JSON to validate format
                test_cases = json.loads(obj.test_cases)
                # Ensure it's in the correct format
                if not isinstance(test_cases, list):
                    test_cases = [test_cases]
                # Ensure each test case has input and expected
                formatted_cases = []
                for test in test_cases:
                    if isinstance(test, dict) and 'input' in test and 'expected' in test:
                        formatted_cases.append(test)
                    else:
                        # Try to format it
                        formatted_cases.append({
                            'input': str(test),
                            'expected': str(test)
                        })
                obj.test_cases = json.dumps(formatted_cases)
            except json.JSONDecodeError:
                # If it's not valid JSON, format it as a simple test case
                obj.test_cases = json.dumps([{
                    'input': obj.test_cases,
                    'expected': obj.test_cases
                }])
        super().save_model(request, obj, form, change)

@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ('user', 'nom', 'prenom', 'email', 'level')
    list_filter = ('level',)
    search_fields = ('nom', 'prenom', 'email')

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'description')

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_domain', 'difficulty', 'points', 'get_is_active')
    list_filter = ('difficulty', 'points')
    search_fields = ('title', 'description')
    list_editable = ('points',)

    def get_domain(self, obj):
        return obj.domain.name
    get_domain.short_description = 'Domain'

    def get_is_active(self, obj):
        return obj.is_active
    get_is_active.short_description = 'Active'
    get_is_active.boolean = True
