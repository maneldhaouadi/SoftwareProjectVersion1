"""
URL configuration for SoftwareProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path,include
from . import views  # importe la vue home


urlpatterns = [
    path('admin/', admin.site.urls),

    # Pages principales
    path('', views.home, name='home'),
    path('index.html', views.home, name='index'),
    path('about.html', views.about, name='about'),
    path('contact.html', views.contact, name='contact'),
    path('blog.html', views.blog, name='blog'),
    path('Doctor.html', views.doctor, name='doctor'),
    path('services.html', views.services, name='services'),
    path('single-blog.html', views.single_blog, name='single-blog'),
    path('', include('MaterialsApp.urls')),  # ici on relie les urls de ton app
    path('dep.html', views.dep, name='depertments'),
    #RendezVousApp URLs
    path('RDV/', include('RendezVousApp.urls')),
    #####

]
