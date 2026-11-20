from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django import forms
import json
import os
import subprocess
import sys
import tempfile

from django.core.files.images import get_image_dimensions
from django.http import JsonResponse
from django.urls import reverse

from .models import Domain, InitialTest, Membre, Problem, Submission

def home(request):
    return render(request, 'coding/home.html')

@login_required
def take_initial_test(request):
    # If user has already completed the test, redirect to problems
    if request.user.membre.has_completed_initial_test:
        return redirect('coding:problems')

    # Create initial test questions if none exist
    create_default_questions()

    # Get questions and render the test
    questions = InitialTest.objects.all()
    questions_json = [{
        'id': q.id,
        'question': q.question,
        'test_cases': q.test_cases,
        'points': q.points,
        'difficulty': q.difficulty
    } for q in questions]

    return render(request, 'coding/initial_test.html', {
        'questions': questions,
        'questions_json': json.dumps(questions_json)
    })

def create_default_questions():
    """
    Create initial test questions if none exist
    """
    if InitialTest.objects.count() == 0:
        questions = [
            # Easy Questions (Difficulty 1)
            {
                "question": "Write a function that returns the square of a number.",
                "test_cases": json.dumps([
                    {"input": "5", "expected": "25"},
                    {"input": "3", "expected": "9"},
                    {"input": "0", "expected": "0"}
                ]),
                "difficulty": 1,
                "points": 10
            },
            {
                "question": "Write a function that returns True if a number is even, and False if it's odd.",
                "test_cases": json.dumps([
                    {"input": "4", "expected": "True"},
                    {"input": "7", "expected": "False"},
                    {"input": "0", "expected": "True"}
                ]),
                "difficulty": 1,
                "points": 10
            },
            {
                "question": "Write a function that returns the sum of digits in a number.",
                "test_cases": json.dumps([
                    {"input": "123", "expected": "6"},
                    {"input": "456", "expected": "15"},
                    {"input": "0", "expected": "0"}
                ]),
                "difficulty": 1,
                "points": 10
            },

            # Medium Questions (Difficulty 2)
            {
                "question": "Write a function that returns the factorial of a number.",
                "test_cases": json.dumps([
                    {"input": "5", "expected": "120"},
                    {"input": "3", "expected": "6"},
                    {"input": "0", "expected": "1"}
                ]),
                "difficulty": 2,
                "points": 20
            },
            {
                "question": "Write a function that returns the nth Fibonacci number (starting with 0 and 1).",
                "test_cases": json.dumps([
                    {"input": "5", "expected": "5"},
                    {"input": "7", "expected": "13"},
                    {"input": "0", "expected": "0"}
                ]),
                "difficulty": 2,
                "points": 20
            },
            {
                "question": "Write a function that checks if a number is prime.",
                "test_cases": json.dumps([
                    {"input": "7", "expected": "True"},
                    {"input": "4", "expected": "False"},
                    {"input": "2", "expected": "True"}
                ]),
                "difficulty": 2,
                "points": 20
            },

            # Hard Questions (Difficulty 3)
            {
                "question": "Write a function that returns the GCD (Greatest Common Divisor) of two numbers.",
                "test_cases": json.dumps([
                    {"input": "48, 18", "expected": "6"},
                    {"input": "54, 24", "expected": "6"},
                    {"input": "7, 13", "expected": "1"}
                ]),
                "difficulty": 3,
                "points": 30
            },
            {
                "question": "Write a function that checks if a number is a palindrome.",
                "test_cases": json.dumps([
                    {"input": "12321", "expected": "True"},
                    {"input": "12345", "expected": "False"},
                    {"input": "11", "expected": "True"}
                ]),
                "difficulty": 3,
                "points": 30
            },
            {
                "question": "Write a function that returns the number of trailing zeros in factorial of a number.",
                "test_cases": json.dumps([
                    {"input": "5", "expected": "1"},
                    {"input": "10", "expected": "2"},
                    {"input": "25", "expected": "6"}
                ]),
                "difficulty": 3,
                "points": 30
            },
            {
                "question": "Write a function that returns the sum of all prime numbers up to n.",
                "test_cases": json.dumps([
                    {"input": "10", "expected": "17"},
                    {"input": "5", "expected": "10"},
                    {"input": "2", "expected": "2"}
                ]),
                "difficulty": 3,
                "points": 30
            }
        ]

        # Delete existing questions (optional)
        InitialTest.objects.all().delete()

        # Create all questions
        for q in questions:
            InitialTest.objects.create(
                question=q["question"],
                test_cases=q["test_cases"],
                difficulty=q["difficulty"],
                points=q["points"]
            )

@login_required
def submit_initial_test(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            question_id = data.get('question_id')

            # Get the question
            question = get_object_or_404(InitialTest, id=question_id)

            # Execute code and check result
            result = execute_code(code, question.test_cases)

            if result['passed']:
                # The initial test score is computed from this list, never from the browser.
                passed = set(request.session.get('initial_test_passed', []))
                passed.add(question.id)
                request.session['initial_test_passed'] = sorted(passed)
                return JsonResponse({
                    'success': True,
                    'output': 'Test cases passed! Moving to next question...',
                    'next_question': True
                })
            else:
                return JsonResponse({
                    'success': False,
                    'output': result['output'],
                    'cases': case_results(result['output']),
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'output': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'output': 'Invalid request'})

@login_required
def problem_detail(request, problem_id):
    problem = get_object_or_404(Problem, id=problem_id)
    return render(request, 'coding/problem_detail.html', {
        'problem': problem
    })

@login_required
def submit_solution(request, problem_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            time_taken = data.get('time_taken', 0)
            time_exceeded = data.get('time_exceeded', False)
            problem = get_object_or_404(Problem, id=problem_id)

            # Execute code and check result
            result = execute_code(code, problem.test_cases)

            already_solved = Submission.objects.filter(
                user=request.user.membre, problem=problem, status='S'
            ).exists()

            if result['passed']:
                # Calculate points based on time; a problem already solved earns nothing more
                if already_solved:
                    points_earned = 0
                elif time_exceeded:
                    points_earned = max(0, problem.points - problem.penalty_points)
                else:
                    points_earned = problem.points

                # Create successful submission
                Submission.objects.create(
                    user=request.user.membre,
                    problem=problem,
                    code=code,
                    status='S',
                    execution_time=time_taken
                )

                # Update user points and check level
                membre = request.user.membre
                membre.points += points_earned
                membre.save()

                # Check for level change
                level_changed, old_level, new_level = membre.update_level()

                response_data = {
                    'success': True,
                    'passed': True,
                    'points': points_earned,
                    'output': 'All test cases passed!',
                    'cases': case_results(result['output']),
                }

                if level_changed:
                    if new_level > old_level:
                        response_data['level_up'] = True
                        response_data['new_level'] = new_level
                    else:
                        response_data['level_down'] = True
                        response_data['new_level'] = new_level

                return JsonResponse(response_data)
            else:
                # Create failed submission
                Submission.objects.create(
                    user=request.user.membre,
                    problem=problem,
                    code=code,
                    status='F',
                    execution_time=time_taken
                )

                return JsonResponse({
                    'success': True,
                    'passed': False,
                    'output': 'Some test cases failed. Keep trying!',
                    'cases': case_results(result['output']),
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
def test_solution(request, problem_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            problem = get_object_or_404(Problem, id=problem_id)

            # Execute code and return result
            result = execute_code(code, problem.test_cases)
            return JsonResponse({
                'success': True,
                'passed': result['passed'],
                'output': 'All test cases passed!' if result['passed'] else 'Some test cases failed. Keep trying!',
                'cases': case_results(result['output']),
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def profile(request):
    membre = request.user.membre
    submissions = Submission.objects.filter(user=membre).order_by('-submission_time')[:10]

    # Calculate problem statistics
    solved_problems = Submission.objects.filter(user=membre, status='S').values('problem').distinct()
    solved_count = solved_problems.count()

    # Calculate progress for each difficulty level
    problems = Problem.objects.all()

    easy_total = problems.filter(difficulty='easy').count()
    medium_total = problems.filter(difficulty='medium').count()
    hard_total = problems.filter(difficulty='hard').count()

    easy_solved = solved_problems.filter(problem__difficulty='easy').count()
    medium_solved = solved_problems.filter(problem__difficulty='medium').count()
    hard_solved = solved_problems.filter(problem__difficulty='hard').count()

    # Calculate percentages
    easy_progress = (easy_solved / easy_total * 100) if easy_total > 0 else 0
    medium_progress = (medium_solved / medium_total * 100) if medium_total > 0 else 0
    hard_progress = (hard_solved / hard_total * 100) if hard_total > 0 else 0

    progress_rows = [
        (label, solved, total, [i < solved for i in range(total)])
        for label, solved, total in (('Easy', easy_solved, easy_total), ('Medium', medium_solved, medium_total),
                                     ('Hard', hard_solved, hard_total))
    ]

    context = {
        'progress_rows': progress_rows,
        'membre': membre,
        'submissions': submissions,
        'solved_count': solved_count,
        'easy_total': easy_total,
        'medium_total': medium_total,
        'hard_total': hard_total,
        'easy_solved': easy_solved,
        'medium_solved': medium_solved,
        'hard_solved': hard_solved,
        'easy_progress': easy_progress,
        'medium_progress': medium_progress,
        'hard_progress': hard_progress,
    }

    return render(request, 'coding/profile.html', context)

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

            membre = Membre(
                user=user,
                nom=form.cleaned_data['nom'],
                prenom=form.cleaned_data['prenom'],
                email=form.cleaned_data['email'],
                telephone=form.cleaned_data.get('telephone', ''),
                level=0
            )
            if form.cleaned_data.get('profile_image'):
                membre.profil = form.cleaned_data['profile_image']
            membre.save()

            login(request, user)
            messages.success(request, 'Registration successful! Please take the initial test.')
            return redirect('coding:initial_test')
    else:
        form = UserRegistrationForm()
    return render(request, 'coding/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Check if user has a membre profile and hasn't taken the test yet
            try:
                membre = user.membre
                if not membre.has_completed_initial_test:
                    messages.info(request, 'Please complete your initial test to continue.')
                    return redirect('coding:initial_test')
                else:
                    return redirect('coding:problems')  # User has taken the test
            except Membre.DoesNotExist:
                messages.error(request, 'User profile not found.')
                return redirect('coding:home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'coding/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('coding:home')

def case_results(output):
    """True/False for each test case, read from the runner output (one line per case)."""
    return [line.startswith('✅') for line in output.splitlines() if line[:1] in ('✅', '❌')]


def execute_code(code, test_cases):
    temp_file = None
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
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)


def _limit_resources():  # runs in the child process, POSIX only
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))  # above the 5 s wall-clock timeout
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))


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
                # shortcut: this limits the damage user code can do but is not a sandbox;
                # run it in a container or a dedicated judge before opening the platform to strangers.
                result = subprocess.run(
                    [sys.executable, '-I', test_file],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=tempfile.gettempdir(),
                    env={'PATH': os.environ.get('PATH', ''), 'SYSTEMROOT': os.environ.get('SYSTEMROOT', '')},
                    preexec_fn=_limit_resources if os.name == 'posix' else None,
                )

                # Compare output with expected result
                actual_output = result.stdout.strip()

                if result.returncode == 0:
                    if actual_output == expected:
                        output.append(f"✅ Test case {i} passed: Input={input_data}, Expected={expected}")
                    else:
                        all_passed = False
                        output.append(f"❌ Test case {i} failed: Input={input_data}, Expected={expected}, Got={actual_output}")
                elif result.returncode < 0:
                    all_passed = False
                    output.append(f"❌ Test case {i} stopped: time or memory limit exceeded")
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

@login_required
def problems_view(request):
    # First, check if user has completed initial test
    if not request.user.membre.has_completed_initial_test:
        return redirect('coding:initial_test')

    solved = set(Submission.objects.filter(user=request.user.membre, status='S').values_list('problem_id', flat=True))
    domains = []
    for domain in Domain.objects.prefetch_related('problems'):
        problems = [p for p in domain.problems.all() if p.is_active]
        for p in problems:
            p.solved = p.id in solved
        if problems:
            domains.append({'domain': domain, 'problems': problems, 'solved': sum(p.solved for p in problems)})
    return render(request, 'coding/problems.html', {'domains': domains})

@login_required
def get_domain_problems(request, domain_id):
    try:
        domain = Domain.objects.get(id=domain_id)

        problems = Problem.objects.filter(domain=domain, is_active=True)

        problems_data = [{
            'id': p.id,
            'title': p.title,
            'description': p.description,
            'difficulty': p.difficulty,
            'points': p.points,
            'completed': Submission.objects.filter(
                user=request.user.membre,
                problem=p,
                status='S'
            ).exists()
        } for p in problems]

        return JsonResponse({
            'success': True,
            'domain_name': domain.name,
            'problems': problems_data,
            'count': len(problems_data)
        })

    except Domain.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Domain with ID {domain_id} not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def complete_initial_test(request):
    # Prevent accessing this view if test is already completed
    if request.user.membre.has_completed_initial_test:
        return JsonResponse({
            'success': False,
            'error': 'Initial test already completed',
            'redirect_url': reverse('coding:problems')
        })

    if request.method == 'POST':
        try:
            passed = request.session.get('initial_test_passed', [])
            total_points = sum(InitialTest.objects.filter(id__in=passed).values_list('points', flat=True))
            max_possible_points = sum(InitialTest.objects.values_list('points', flat=True)) or 1
            score_percentage = (total_points / max_possible_points) * 100

            # Determine level based on performance
            if score_percentage >= 80:
                level = 3
                level_message = "Expert"
            elif score_percentage >= 50:
                level = 2
                level_message = "Intermediate"
            else:
                level = 1
                level_message = "Beginner"

            # Update user's profile
            membre = request.user.membre
            membre.level = level
            membre.points = total_points
            membre.has_completed_initial_test = True
            membre.save()
            request.session.pop('initial_test_passed', None)

            return JsonResponse({
                'success': True,
                'level': level_message,
                'points': total_points,
                'redirect_url': reverse('coding:problems'),
                'message': f"Initial test finished. Level: {level_message}"
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def give_up_problem(request, problem_id):
    if request.method == 'POST':
        try:
            problem = get_object_or_404(Problem, id=problem_id)
            membre = request.user.membre

            # Fixed penalty of 20 points
            points_deducted = 20

            # Create a failed submission
            Submission.objects.create(
                user=membre,
                problem=problem,
                code="[Gave up]",
                status='F',
                execution_time=None
            )

            # Deduct points and update level
            membre.points = max(0, membre.points - points_deducted)
            membre.save()

            # Check for level change
            level_changed, old_level, new_level = membre.update_level()

            response_data = {
                'success': True,
                'points_deducted': points_deducted,
                'new_total_points': membre.points
            }

            if level_changed:
                response_data['level_down'] = True
                response_data['new_level'] = new_level

            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })
