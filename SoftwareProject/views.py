from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def blog(request):
    return render(request, 'blog.html')

def doctor(request):
    return render(request, 'doctor.html')

def services(request):
    return render(request, 'services.html')

def single_blog(request):
    return render(request, 'single-blog.html')

def dep(request):
    return render(request, 'dep.html')
