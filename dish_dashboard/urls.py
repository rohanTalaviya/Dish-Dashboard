from django.contrib import admin
from django.urls import path
from . import views
from AI.modeldata import get_restaurant_model_dish_list
from django.views.generic import TemplateView
from .views import restaurants, restaurant_model_data
from AI.dish_edit_details import get_dish_details, update_dish_fields, run_model, suggest_ingredient_name
from AI.restaurant_list import get_restaurant_list, get_restaurant_dish_list, get_dish_names
from AI.error_data_handling import get_error_model_dish_list
from AI.modeldata import get_model_dish_list


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage),
    path('get_error_model_dish_list/', get_error_model_dish_list, name='get_error_model_dish_list'),
    path('get_model_dish_list/', get_model_dish_list, name='get_model_dish_list'),
    path('get_restaurant_model_dish_list/', get_restaurant_model_dish_list, name='get_restaurant_model_dish_list'),
    path('modeldatalist.html', TemplateView.as_view(template_name="modeldatalist.html"), name='modeldatalist'),
    path('restaurantmodeldata.html', TemplateView.as_view(template_name="restaurantmodeldata.html"), name='restaurantmodeldata'),
    path('modeldata.html', TemplateView.as_view(template_name="modeldata.html"), name='modeldata'),
    path('restaurants/', restaurants, name='restaurants'),
    path('restaurantmodeldata/', restaurant_model_data, name='restaurantmodeldata'),
    path('dish_edit_details.html', TemplateView.as_view(template_name="dish_edit_details.html"), name='dish_edit_details'),
    path('get_dish_details/', get_dish_details, name='get_dish_details'),
    path('update_dish_fields/', update_dish_fields, name='update_dish_fields'),
    path('get_restaurant_list/', get_restaurant_list, name='get_restaurant_list'),
    path('get_restaurant_dish_list/', get_restaurant_dish_list, name='get_restaurant_dish_list'),
    path('get_dish_names/', get_dish_names, name='get_dish_names'),
    path('restaurants_list.html', TemplateView.as_view(template_name="restaurants_list.html"), name='restaurants_list'),
    path('restaurantdishlist.html', TemplateView.as_view(template_name="restaurantdishlist.html"), name='restaurantdishlist'),
    path('run_model/', run_model, name='run_model'),
    path('suggest_ingredient_name/', suggest_ingredient_name, name='suggest_ingredient_name'),
    path('verification_dish_data.html', TemplateView.as_view(template_name="verification_dish_data.html"), name='verification_dish_data'),
]
