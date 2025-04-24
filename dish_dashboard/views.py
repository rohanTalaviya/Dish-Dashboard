from django.shortcuts import render
from django.http import HttpResponse

def homepage(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def restaurants(request):
    return render(request, 'restaurants.html')

def restaurant_model_data(request):
    return render(request, 'restaurantmodeldata.html')

def restaurant_model_data(request):
    return render(request, 'modeldata.html')