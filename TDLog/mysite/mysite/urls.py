"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Coding.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_page, name='home'),  # It's a good idea to give your main URL a name
    path('details/', details_page, name='details'),
    path('browse/', browse_page, name='browse'),
    path('streams/', streams_page, name='streams'),
    path('profile/', profile_page, name='profile'),  # Ensure this is set up correctly
]