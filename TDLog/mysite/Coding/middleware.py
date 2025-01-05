from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages

class InitialTestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_url = resolve(request.path_info).url_name
            if current_url == 'initial_test' and request.user.membre.has_completed_initial_test:
                messages.warning(request, 'Vous avez déjà complété le test initial.')
                return redirect('coding:problems')
        return self.get_response(request) 