from django.shortcuts import render

def home(request):
    return render(request, 'coding/home.html')

def details_page(request):
    return render(request, 'details.html')

def browse_page(request):
    return render(request, 'browse.html')

def streams_page(request):
    return render(request, 'streams.html')

def profile_page(request):
    return render(request, 'profile.html')
