from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import *
import json
from django.core.files.images import get_image_dimensions
from django.http import JsonResponse
import subprocess
import tempfile
import os
from django.conf import settings
from django.urls import reverse


def home(request):
    return render(request, 'coding/home.html')

def execute_code(code, test_cases):
    try:
        # Parse test cases if they're in string format
        if isinstance(test_cases, str):
            test_cases = json.loads(test_cases)
        
        # Create a temporary file for the code using raw string for path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write the user's solution function
            f.write(code + '\n\n')
            temp_file = f.name.replace('\\', '/')  # Convert backslashes to forward slashes
        
        # Run test cases
        test_results = run_test_cases(temp_file, test_cases)
        return test_results

    except json.JSONDecodeError:
        return {
            'passed': False,
            'output': 'Error: Invalid test case format'
        }
    except Exception as e:
        return {
            'passed': False,
            'output': f'Error executing code: {str(e)}'
        }
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.remove(temp_file)

@login_required
def profile(request):
    membre = request.user.membre
    submissions = Submission.objects.filter(user=membre).order_by('-submission_time')
    return render(request, 'coding/profile.html', {
        'membre': membre,
        'submissions': submissions
    })

class UserRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()
    nom = forms.CharField(max_length=50)
    prenom = forms.CharField(max_length=50)
    telephone = forms.CharField(max_length=20, required=False)
    profile_image = forms.ImageField(required=False)

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')
        if image:
            w, h = get_image_dimensions(image)
            if w > 4096 or h > 4096:
                raise forms.ValidationError("Image is too large")
            return image
        return None
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        # Check if username already exists
        username = cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        
        return cleaned_data

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
            )
            
            # Get the profile image or use default
            profile_image = form.cleaned_data.get('profile_image')
            if not profile_image:
                profile_image = 'default_profile.jpg'  # Make sure this file exists in your media folder
            
            # Create the associated Membre
            Membre.objects.create(
                user=user,
                nom=form.cleaned_data['nom'],
                prenom=form.cleaned_data['prenom'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data.get('telephone', ''),
                profil=profile_image,
                level=0
            )
            
            login(request, user)
            messages.success(request, 'Registration successful! Please take the initial test.')
            return redirect('coding:initial_test')
    else:
        form = UserRegistrationForm()
    return render(request, 'coding/register.html', {'form': form})


def run_test_cases(code_file, test_cases):
    all_passed = True
    output = []

    try:
        # If test_cases is a string, try to parse it as JSON
        if isinstance(test_cases, str):
            test_cases = json.loads(test_cases)
        
        # If test_cases is a single test case, wrap it in a list
        if isinstance(test_cases, dict):
            test_cases = [test_cases]
        
        # If test_cases is a list of strings, convert to dict format
        if test_cases and isinstance(test_cases[0], str):
            test_cases = [{"input": test, "expected": test_cases[i+1]} 
                         for i, test in enumerate(test_cases[::2])]

        for i, test in enumerate(test_cases, 1):
            # Ensure test is a dictionary
            if isinstance(test, str):
                try:
                    test = json.loads(test)
                except json.JSONDecodeError:
                    output.append(f"❌ Test case {i} error: Invalid test case format")
                    all_passed = False
                    continue

            input_data = str(test.get('input', ''))
            expected = str(test.get('expected', ''))

            # Create a test runner file with proper path handling
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Import the solution code using raw string
                f.write(f'with open(r"{code_file}", "r") as source:\n')
                f.write('    exec(source.read())\n\n')
                # Add the test case
                f.write(f'result = solution({input_data})\n')
                f.write('print(str(result))\n')
                test_file = f.name.replace('\\', '/')  # Convert backslashes to forward slashes

            try:
                # Execute the test
                result = subprocess.run(
                    ['python', test_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Compare output with expected result
                actual_output = result.stdout.strip()
                
                if result.returncode == 0:
                    if actual_output == expected:
                        output.append(f"✅ Test case {i} passed: Input={input_data}, Expected={expected}")
                    else:
                        all_passed = False
                        output.append(f"❌ Test case {i} failed: Input={input_data}, Expected={expected}, Got={actual_output}")
                else:
                    all_passed = False
                    output.append(f"❌ Test case {i} error: {result.stderr}")

            except subprocess.TimeoutExpired:
                all_passed = False
                output.append(f"❌ Test case {i} timed out")
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)

    except Exception as e:
        return {
            'passed': False,
            'output': f'Error running tests: {str(e)}\nTest cases format: {test_cases}'
        }

    return {
        'passed': all_passed,
        'output': '\n'.join(output)
    }