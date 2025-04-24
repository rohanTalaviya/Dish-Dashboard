from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
from rapidfuzz import process, fuzz
import google.generativeai as genai
import json
import re
import requests
import random 

# MongoDB connection
MONGO_URI = "mongodb://Kishan:KishankFitshield@ec2-13-233-104-209.ap-south-1.compute.amazonaws.com:27017/?authMechanism=SCRAM-SHA-256&authSource=Fitshield"
client = MongoClient(MONGO_URI)
db = client["Fitshield"]
ModelData = db["ModelData"]
RestroModelData = db["RestroModelData"]
RestaurantMenuData = db["RestaurantMenuData"]
nutrients_collection = db["Nutrients2"]

# Normalize food name
def normalize_food_name(food_name):
    return re.sub(r'\s?\(.*?\)', '', food_name).strip().lower()

# Find ingredient name using fuzzy matching
def find_ingredient_name(partial_name):
    data = list(nutrients_collection.find({}, {'_id': 0, 'Food name': 1}))
    partial_name_no_spaces = partial_name.replace(" ", "").strip().lower()
    food_names = [normalize_food_name(food['Food name']) for food in data]
    matches = process.extract(partial_name_no_spaces, food_names, limit=10, scorer=fuzz.WRatio)
    filtered_matches = [match for match in matches if match[1] >= 65]

    if not filtered_matches:
        return "No close match found"

    for match in filtered_matches:
        original_food_name = data[food_names.index(match[0])]['Food name']
        if normalize_food_name(original_food_name).startswith(partial_name_no_spaces):
            return original_food_name
    best_match = filtered_matches[0]
    return data[food_names.index(best_match[0])]['Food name']

# Check ingredient correctness using generative AI
def check_ingredient(ingredient_name, db_ingredient_name):
    genai.configure(api_key="AIzaSyC7PuTD0r_KKmKwqcnqpZTeA0-84bOSj24")
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction="You are an ingredient name validator. Your job is to check whether the found ingredient from a database is a correct match for the original ingredient name given by the user.\n\nReturn only true or false.\n\nConsider factors like spelling variations, synonyms, and common naming conventions. Do not explain your reasoning or provide any additional output. Just return true if it’s a valid match, otherwise return false.",
    )
    chat_session = model.start_chat()
    response = chat_session.send_message(f"Original: {ingredient_name}, Found: {db_ingredient_name}")
    response_text = response.text.strip().lower()
    return response_text if response_text in ["true", "false"] else "false"

dish_details = []
# Get dish details and validate ingredients
def get_dish_details(request):
    dish_name = request.GET.get('dish_name')
    source = request.GET.get('source')
    restaurant_id = request.GET.get('restaurant_id')

    # Determine the collection to use based on the source
    if source == 'restaurantdishlist':
        if not restaurant_id:
            return JsonResponse({'error': 'restaurant_id is required for restaurantdishlist source'}, status=400)
        dish_details = RestaurantMenuData.find_one(
            {"_id": restaurant_id,"menu.dish_name": dish_name },
            {"menu.$": 1,"_id": 0}
        )
        if dish_details and "menu" in dish_details:
            dish_details = dish_details["menu"][0]
    elif source == 'restaurantmodeldata':
        dish_details = RestroModelData.find_one({'dish_name': dish_name}, {'_id': 0})
    elif source == 'modeldatalist':
        dish_details = ModelData.find_one({'dish_name': dish_name}, {'_id': 0})
    else:
        return JsonResponse({'error': 'Invalid source parameter'}, status=400)

    if not dish_details:
        return JsonResponse({'error': 'Dish not found'}, status=404)

    # Add db_ingredient_name to each ingredient
    for ingredient in dish_details['dish_variants']['normal']['full']['ingredients']:
        ingredient['db_ingredient_name'] = find_ingredient_name(ingredient['name'])

    # Include price in the response
    price = dish_details['dish_variants']['normal']['full'].get('price', 0)
    dish_details['price'] = price

    # Return the updated dish_details object
    return JsonResponse({'dish_details': dish_details})

def generate_ingredient_id(ingredient_name):
    random_digits = random.randint(1000, 99999)
    ingredient_id = f"{ingredient_name.replace(' ', '_')}_{random_digits}"
    return ingredient_id

def update_origin_ingredients(ingredients, origin_ingredient):
    updated_origin = []

    for ing in ingredients:
        # Match by name (case-insensitive)
        match = next((oi for oi in origin_ingredient if oi['name'].lower() == ing['name'].lower()), None)

        if match:
            # Copy and update fields
            updated = match.copy()
            updated.update({
                "name": ing['name'],
                "quantity": ing['quantity'],
                "unit": ing['unit'],
                "description": ing['description']
            })
            # Remove db_ingredient_name if it exists
            updated.pop("db_ingredient_name", None) 
            updated_origin.append(updated)
        else:
            # Add as new ingredient with default metadata
            updated_origin.append({
                "id": generate_ingredient_id(ing['name']),
                "name": ing['name'],
                "quantity": ing['quantity'],
                "unit": ing['unit'],
                "description": ing['description'],
                "is_swappable": False,
                "is_close": True,  
                "is_hide": False,
                "swap_items": [],
                "min_value": 0,
                "max_value": 10000
            })

    return updated_origin

@csrf_exempt
def update_dish_fields(request):
    if request.method == 'POST':
        try:
            # Parse the request body
            data = json.loads(request.body)
            print("Received data:", data)  # Debugging log
            dish_name = data.get('dish_name')
            updates = data.get('updates', {})
            source = data.get('source')
            restaurant_id = data.get('restaurant_id')

            # Debugging logs
            print("Received update request for dish:", dish_name)
            print("Updates:", updates)
            print("Source:", source)

            if not dish_name or not updates:
                return JsonResponse({'error': 'Dish name and updates are required'}, status=400)

            # Ensure complementary_dishes is updated correctly
            if 'complementary_dishes' in updates:
                updates['complementary_dishes'] = updates['complementary_dishes']

            # Ensure price is updated correctly
            if 'price' in updates:
                updates['dish_variants.normal.full.price'] = updates.pop('price')

            # Determine the collection and update logic based on the source
            if source == 'restaurantdishlist':
                if not restaurant_id:
                    return JsonResponse({'error': 'restaurant_id is required for restaurantdishlist source'}, status=400)
                result = RestaurantMenuData.update_one(
                    {"_id": restaurant_id, "menu.dish_name": dish_name},
                    {"$set": {f"menu.$.{key}": value for key, value in updates.items()}}
                )

            elif source == 'restaurantmodeldata':
                result = RestroModelData.update_one(
                    {'dish_name': dish_name},
                    {'$set': updates}
                )

            elif source == 'modeldatalist':
                result = ModelData.update_one(
                    {'dish_name': dish_name},
                    {'$set': updates}
                )

            else:
                return JsonResponse({'error': 'Invalid source parameter'}, status=400)

            if result.matched_count == 0:
                return JsonResponse({'error': 'Dish not found or no updates applied'}, status=404)

            return JsonResponse({'success': True, 'message': 'Dish fields updated successfully'})
        except Exception as e:
            print("Error updating dish fields:", str(e))  # Debugging log for errors
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def run_model(request):
    if request.method == 'POST':
        try:
            # Parse the request body
            data = json.loads(request.body)
            print("Received payload for run_model:", data)  # Debugging log

            # Validate required fields
            restro_id = data.get('restaurant_id')
            dish_id = data.get('dishId')
            ingredients = data.get('ingredients')
            cooking_style = data.get('cooking_style')
            origin_ingredient = data.get('origin_ingredient')
            origin_ingredient = update_origin_ingredients(ingredients, origin_ingredient)  # Update origin ingredients

            if not restro_id or not dish_id or not ingredients:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: restro_id, dish_id, or ingredients'
                }, status=400)

            # Validate ingredients structure
            for ingredient in ingredients:
                if not all(key in ingredient for key in ['name', 'quantity', 'unit']):
                    return JsonResponse({
                        'success': False,
                        'error': 'Each ingredient must have name, quantity, and unit'
                    }, status=400)

            url = 'https://production.fitshield.in/api/update-dish'
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {
                "restro_id": restro_id,
                "dish_id": dish_id,
                "updated_fields": {
                    "full": {
                        "ingredients": origin_ingredient
                    },
                    "cooking_style": cooking_style
                }
            }

            try:
                response = requests.put(url, headers=headers, json=payload)
                if response.status_code == 400:
                    print("External API returned 400:", response.json())
                response.raise_for_status() 
                return JsonResponse(response.json()) 
            except requests.exceptions.RequestException as e:
                return JsonResponse({"error": str(e)}, status=500) 
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def suggest_ingredient_name(request):
    partial_name = request.GET.get('partial_name', '').strip()
    if not partial_name:
        return JsonResponse({'suggestions': []})

    # Call the suggest_ingredient_name function
    suggestions = suggest_ingredient_name_function(partial_name)
    return JsonResponse({'suggestions': suggestions})

def suggest_ingredient_name_function(partial_name):
    """Suggest top 10 food names based on partial input using fuzzy matching with exact match priority."""
    data = list(nutrients_collection.find({}, {'_id': 0, 'Food name': 1}))
    partial_name_no_spaces = partial_name.replace(" ", "").strip().lower()
    food_names = [normalize_food_name(food['Food name']) for food in data]
    matches = process.extract(partial_name_no_spaces, food_names, limit=5, scorer=fuzz.WRatio)
    filtered_matches = [match for match in matches if match[1] >= 65]

    if not filtered_matches:
        return ["No close match found"]

    top_matches = []
    for match in filtered_matches:
        index = food_names.index(match[0])
        original_food_name = data[index]['Food name']
        top_matches.append(original_food_name)

    return top_matches
