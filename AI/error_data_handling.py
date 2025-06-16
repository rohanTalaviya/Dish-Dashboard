from django.http import JsonResponse
from AI.connection import db

# MongoDB connection
ErrorDishData = db["ErrorDishData"]


# Function to calculate nutrient values for an ingredient
def get_error_model_dish_list(request):
    error_dish_data = list(ErrorDishData.find({}, {'_id': 0}))
    print("Error Dish Data:", error_dish_data)
    return JsonResponse({'error_dish_data': error_dish_data})

