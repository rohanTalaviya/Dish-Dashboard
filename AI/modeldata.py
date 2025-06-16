from django.http import JsonResponse
from AI.connection import db

# MongoDB connection
ModelData = db["ModelData"]
RestroModelData = db["RestroModelData"]

# Function to calculate nutrient values for an ingredient
def get_model_dish_list(request):
    dish_list = list(ModelData.find({}, {'_id': 0, 'dish_name': 1}))
    return JsonResponse({'data_list': dish_list})

def get_restaurant_model_dish_list(request):
    dish_list = list(RestroModelData.find({}, {'_id': 0, 'dish_name': 1}))
    return JsonResponse({'data_list': dish_list})
