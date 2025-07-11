import json
import re
import requests
import uuid
import copy
from AI.connection import db
from django.http import JsonResponse
from rapidfuzz import process, fuzz
import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

# MongoDB connection
ModelData = db["ModelData"]
RestroModelData = db["RestroModelData"]
RestaurantMenuData = db["RestaurantMenuData"]
nutrients_collection = db["Nutrients"]
ingredients_db_names = list(nutrients_collection.find({}, {'_id': 0, 'food_name': 1}))

# Nutritionix API Credentials
APP_ID = "c5c1581f"
API_KEY = "cd6145d5b423027bff17ea8940dd3df7"

aa_text="""You are a culinary AI assistant that compares two ingredient lists of the same dish — one from a homemade (cousin) version and one from a restaurant version.

You will receive structured JSON input with two keys:

"homemade_ingredients": List of ingredients used in the homemade version.

"restaurant_ingredients": List of ingredients used in the restaurant version.

Your task is to:

1. Identify ingredient alternatives
Match ingredients across the two lists that may not be identical in name but are functional substitutes.

Consider culinary role (fat, sweetener, spice, etc.), taste, texture, or usage.

Examples: "ghee" ↔ "butter", "honey" ↔ "sugar", "green peas" ↔ "peas", "capsicum" ↔ "bell pepper".

Ignore ingredients that are exact string matches.

2. Identify missing ingredients
List ingredients that appear in one version and have no equivalent in the other.

Do not list exact matches or alternatives here.

✅ Output format (always return this structure):
{
  "alternatives": [
    {
      "homemade": "ghee",
      "restaurant": "butter"
    }
  ],
  "missing_in_homemade": ["carrot"],
  "missing_in_restaurant": ["cauliflower"]
}
⚠️ Notes:

Do not include exact matches in alternatives.

Do not include ingredients that are already part of alternatives in the missing lists.

Do not explain your reasoning — return only the JSON output.

Treat ingredient pairs as valid alternatives if they represent the same core item but differ in form, preparation state, or description — e.g., “potato” vs “boiled potatoes”, “red chilli” vs “red chillies”, “onion” vs “spring onion”, "Garam masala" vs "Dish masala".
"""

dish_details = []

# Normalize text for fuzzy matching
def normalize(text):
    text = re.sub(r'\s?\(.*?\)', '', text).strip().lower()
    return ' '.join([stemmer.stem(word) for word in text.split()])

def find_ingredient_name(partial_name, threshold=90):
    user_input = normalize(partial_name)
    db_names = [normalize(food['food_name']) for food in ingredients_db_names]

    matches = process.extract(user_input, db_names, scorer=fuzz.token_sort_ratio, limit=10)

    good_matches = [m for m in matches if m[1] >= threshold]

    if good_matches:
        idx = db_names.index(good_matches[0][0])
        return ingredients_db_names[idx]['food_name']

    suggestion = suggest_five_ingredient_name(partial_name)
    return f"No match : {suggestion}"

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
    random_digits = uuid.uuid4()
    ingredient_id = f"{ingredient_name.replace(' ', '')}_{random_digits}" 
    return ingredient_id

def custom_round(input_str: str) -> str:
    number = float(input_str)
    
    if number < 5:
        result = float(int(number) + 1)
    else:
        remainder = number % 5
        base = number - remainder
        if remainder >= 2.5:
            result = base + 5
        else:
            result = base
            
    return input_str

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
                "quantity": custom_round(ing['quantity']),
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
                "quantity": custom_round(ing['quantity']),
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
            dish_name = data.get('dish_name')
            updates = data.get('updates', {})
            source = data.get('source')
            restaurant_id = data.get('restaurant_id')

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
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def run_model(request):
    if request.method == 'POST':
        try:
            # Parse the request body
            data = json.loads(request.body)

            # Validate required fields
            restro_id = data.get('restaurant_id')
            dish_id = data.get('dishId')
            dish_name = data.get('dish_name')
            ingredients = data.get('ingredients')
            cooking_style = data.get('cooking_style')
            origin_ingredient = data.get('origin_ingredient')
            origin_ingredient = update_origin_ingredients(ingredients, origin_ingredient)  # Update origin ingredients


            # Validate ingredients structure
            for ingredient in ingredients:
                if not all(key in ingredient for key in ['name', 'quantity', 'unit']):
                    return JsonResponse({
                        'success': False,
                        'error': 'Each ingredient must have name, quantity, and unit'
                    }, status=400)
            
           
            if restro_id:
                if not dish_id or not ingredients:
                    return JsonResponse({
                        'success': False,
                        'error': 'Missing required fields: dish_id or ingredients'
                    }, status=400)

                url = 'https://production.fitshield.in/api/update-dish'
                headers = {
                    'Content-Type': 'application/json'
                }
                headers['Authorization'] = f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZml0c2hpZWxkX3VzZXJfMTQ1ZGUwODJlZjdkNDJmZSIsInNvdXJjZSI6ImFwcCIsImlhdCI6MTc0OTIwOTg3OSwiZXhwIjoxNzUxODAxODc5fQ.Ky4LR3MBQC8UfQmKeNelkFgPmzEX4bFJG9n4vVG2dk0"
                payload = {
                    "restro_id": restro_id,
                    "dish_id": dish_id,
                    "is_admin": True,
                    "updated_fields": {
                        "full": {
                            "ingredients": origin_ingredient
                        },
                        "cooking_style": cooking_style
                    }
                }

            else:

                if not ingredients:
                    return JsonResponse({
                        'success': False,
                        'error': 'Missing required fields: ingredients'
                    }, status=400)
                
                url = "https://sandbox.fitshield.in/api/auto-update-model-dish"
                #url = "https://production.fitshield.in/api/auto-update-model-dish"
                headers = {
                    'Content-Type': 'application/json'
                }
                payload = {
                    "dish_name": dish_name,
                    "updated_fields": {
                        "full": {
                            "ingredients": origin_ingredient
                        },
                        "cooking_style": cooking_style
                    }
                }

            try:
                response = requests.put(url, headers=headers, json=payload)
                print("Response:", response.text)
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

# === Suggest Ingredient Name ===

@csrf_exempt
def update_main_data(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dish_name = data.get('dish_name')
            ingredients = data.get('ingredients', [])
            cooking_style = data.get('cooking_style', '')
            model_data_dish = ModelData.find_one({'dish_name': dish_name})

            # Your main data
            model_ingredients = model_data_dish["dish_variants"]["normal"]["full"]["ingredients"]
            # Someone else's data
            restaurant_ingredients = ingredients

            # Step 1: Get Gemini's suggestion
            gemini_output = generate_replacements(model_ingredients, restaurant_ingredients)

            # Step 2: Add replacements to your data only
            updated_model_ingredients = add_potential_replacements_to_model(model_ingredients, gemini_output, restaurant_ingredients)
            
            # Step 2.5: Add unmatched restaurant ingredients not used as replacements
            updated_model_ingredients, newly_added = append_strictly_unmatched_ingredients(
                updated_model_ingredients, restaurant_ingredients, gemini_output
            )
            print("✅ Strictly unmatched ingredients added:", newly_added)
            print("Updated model ingredients:", updated_model_ingredients)

            # Prepare payload for external API
            payload = {
                "dish_name": dish_name,
                "updated_fields": {
                    "full": {
                        "ingredients": updated_model_ingredients
                    },
                    "cooking_style": cooking_style
                }
            }
            url = "https://sandbox.fitshield.in/api/auto-update-model-dish"
            headers = {'Content-Type': 'application/json'}

            response = requests.put(url, headers=headers, json=payload)
            return JsonResponse(response.json(), status=response.status_code)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def normalize_name(name):
    return name.strip().lower()

def add_potential_replacements_to_model(model_ingredients, gemini_output, restaurant_ingredients):
    enriched = copy.deepcopy(model_ingredients)
    name_to_model_item = {normalize_name(ing["name"]): ing for ing in enriched}
    restaurant_name_set = {normalize_name(r["name"]) for r in restaurant_ingredients}

    # Ensure all have a dict
    for ing in enriched:
        if "potential_replacement" not in ing or not isinstance(ing["potential_replacement"], dict):
            ing["potential_replacement"] = {}

    # 1. Add Gemini-suggested alternatives
    for alt in gemini_output.get("alternatives", []):
        homemade_name = normalize_name(alt["homemade"])
        restaurant_name = alt["restaurant"]

        if homemade_name in name_to_model_item:
            rep_map = name_to_model_item[homemade_name]["potential_replacement"]
            rep_map[restaurant_name] = rep_map.get(restaurant_name, 0) + 1

    # 2. Add exact matches as replacements
    for model_ing in enriched:
        model_name = model_ing["name"]
        norm_name = normalize_name(model_name)

        if norm_name in restaurant_name_set:
            rep_map = model_ing["potential_replacement"]
            rep_map[model_name] = rep_map.get(model_name, 0) + 1

    return enriched

def append_strictly_unmatched_ingredients(model_ingredients, restaurant_ingredients, gemini_output):
    # Set of normalized names in the model
    model_names = {normalize_name(ing["name"]) for ing in model_ingredients}
    
    # Set of restaurant ingredients already used as potential_replacement
    matched_restaurant_names = {
        normalize_name(item["restaurant"]) for item in gemini_output.get("alternatives", [])
    }

    added = []

    for r_ing in restaurant_ingredients:
        r_name = normalize_name(r_ing.get("name", ""))
        
        # Skip if name is empty or other required fields are missing
        if not r_name or not r_ing.get("quantity") or not r_ing.get("unit"):
            continue

        if r_name not in model_names and r_name not in matched_restaurant_names:
            new_ingredient = copy.deepcopy(r_ing)
            new_ingredient["potential_replacement"] = []
            model_ingredients.append(new_ingredient)
            added.append(new_ingredient["name"])


    return model_ingredients, added

# Configure your API key
genai.configure(api_key="AIzaSyBhRLM3zVcTNBN-MXYhqs9zTz9D0Jb7Jp0")

def generate_replacements(model_ingredients, resurant_ingredients):
    # Prepare the input as JSON string
    input_json = {
        "homemade_ingredients": [m["name"] for m in model_ingredients],
        "restaurant_ingredients": [r["name"] for r in resurant_ingredients],
    }

    # Set up the model
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-04-17",  # or "gemini-pro", "gemini-1.5-pro", etc.
        system_instruction=aa_text
    )

    # Generate content
    response = model.generate_content(
        json.dumps(input_json),
        generation_config={"response_mime_type": "application/json"}
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("Gemini response is not valid JSON:\n" + response.text)



# === Suggest Ingredient Name ===

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
    data = list(nutrients_collection.find({}, {'_id': 0, 'food_name': 1}))
    partial_name_no_spaces = partial_name.replace(" ", "").strip().lower()
    food_names = [normalize(food['food_name']) for food in data]
    matches = process.extract(partial_name_no_spaces, food_names, limit=10, scorer=fuzz.WRatio)
    filtered_matches = [match for match in matches if match[1] >= 65]

    if not filtered_matches:
        return ["No match"]

    top_matches = []
    for match in filtered_matches:
        index = food_names.index(match[0])
        original_food_name = data[index]['food_name']
        top_matches.append(original_food_name)

    return top_matches

def suggest_five_ingredient_name(partial_name):
    """Suggest top 5 food names based on partial input using fuzzy matching with exact match priority."""
    data = list(nutrients_collection.find({}, {'_id': 0, 'food_name': 1}))
    partial_name_no_spaces = partial_name.replace(" ", "").strip().lower()
    food_names = [normalize(food['food_name']) for food in data]
    matches = process.extract(partial_name_no_spaces, food_names, limit=5, scorer=fuzz.WRatio)
    filtered_matches = [match for match in matches if match[1] >= 65]

    if not filtered_matches:
        return ["No match"]

    top_matches = []
    for match in filtered_matches:
        index = food_names.index(match[0])
        original_food_name = data[index]['food_name']
        top_matches.append(original_food_name)

    return top_matches


# === Verify Dish Data ===

@require_GET
def verify_dish_data(request):
    dish_name = request.GET.get('dish_name')
    source = request.GET.get('source')
    restaurant_id = request.GET.get('restaurant_id')

    # Determine the collection to use based on the source
    if source == 'restaurantdishlist':
        if not restaurant_id:
            return JsonResponse({'success': False, 'error': 'restaurant_id is required for restaurantdishlist source'})
        dish_data, dish_nutrients = get_dish_data(RestaurantMenuData, restaurant_id, dish_name)
    elif source == 'restaurantmodeldata':
        dish = RestroModelData.find_one({'dish_name': dish_name}, {'_id': 0})
        if dish:
            dish_data = ', '.join(f"{item['quantity']} {item['unit']} {item['name']}" for item in dish['dish_variants']['normal']['full']['ingredients'])
            dish_nutrients = dish['dish_variants']['normal']['full']['nutrients']
        else:
            dish_data, dish_nutrients = None, None
    elif source == 'modeldatalist':
        dish = ModelData.find_one({'dish_name': dish_name}, {'_id': 0})
        if dish:
            dish_data = ', '.join(f"{item['quantity']} {item['unit']} {item['name']}" for item in dish['dish_variants']['normal']['full']['ingredients'])
            dish_nutrients = dish['dish_variants']['normal']['full']['nutrients']
        else:
            dish_data, dish_nutrients = None, None
    else:
        return JsonResponse({'success': False, 'error': 'Invalid source parameter'})

    if not dish_data or not dish_nutrients:
        return JsonResponse({'success': False, 'error': 'Dish not found'})

    nutritionix_data = get_nutritionix_summary(dish_data)
    if "error" in nutritionix_data:
        return JsonResponse({'success': False, 'error': nutritionix_data["error"]})

    # Prepare comparison result as a list of dicts
    nutrient_map = {
        "ENERC":"nf_calories",
        "PROTCNT": "nf_protein",
        "FATCE": "nf_total_fat",
        "CHOAVLDF": "nf_total_carbohydrate",
        "FIBTG": "nf_dietary_fiber",
        "TOTALFREESUGARS": "nf_sugars",
        "CHOLC": "nf_cholesterol",
        "NA": "nf_sodium"
    }
    system_dict = {item["name"]: item for item in dish_nutrients}
    comparison = []
    percent_diffs = []
    avg_nutrients = ["ENERC", "PROTCNT", "FATCE", "CHOAVLDF", "FIBTG"]
    for sys_key, nutrx_key in nutrient_map.items():
        system_value = system_dict.get(sys_key, {}).get("quantity", 0)
        nutritionix_value = nutritionix_data.get(nutrx_key, 0)
        unit = system_dict.get(sys_key, {}).get("unit", "")
        difference = round(system_value - nutritionix_value, 2)

        # Avoid division by zero for percentage difference
        if nutritionix_value != 0:
            percent_diff = round((difference / nutritionix_value) * 100, 2)
        else:
            percent_diff = None  # or set to 0, or a string like "N/A"

        # Collect percent_diff for average if in avg_nutrients and not None
        if sys_key in avg_nutrients and percent_diff is not None:
            percent_diffs.append(abs(percent_diff))

        comparison.append({
            "nutrient": sys_key,
            "system_value": system_value,
            "nutritionix_value": nutritionix_value,
            "difference": difference,
            "percent_difference": percent_diff,
            "unit": unit
        })

    # Calculate average percent mismatch
    avg_percent_mismatch = round(sum(percent_diffs) / len(percent_diffs), 2) if percent_diffs else None

    return JsonResponse({'success': True, 'comparison': comparison, 'average_percent_mismatch': avg_percent_mismatch})

def get_dish_data(collection, target_id, dish_name):
    result = collection.find_one(
        {
            "_id": target_id,
            "menu.dish_name": dish_name
        },
        {
            "menu.$": 1,
            "_id": 0
        }
    )

    if result and "menu" in result:
        try:
            dish_data = result["menu"][0]["dish_variants"]["normal"]["full"]
            ingredients = dish_data["ingredients"]
            nutrients = dish_data["nutrients"]
            formatted_string = ', '.join(f"{item['quantity']} {item['unit']} {item['name']}" for item in ingredients)
            return formatted_string, nutrients
        except (KeyError, IndexError, TypeError) as e:
            print("Error extracting dish data:", e)
            return None, None
    return None, None

def get_nutritionix_summary(query):
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": APP_ID,
        "x-app-key": API_KEY,
        "Content-Type": "application/json"
    }
    print(query)
    response = requests.post(url, headers=headers, json={"query": query})

    if response.status_code != 200:
        return {"error": f"{response.status_code} - {response.text}"}

    result = response.json()
    total_nutrients = {}

    for food in result.get("foods", []):
        for nutrient, value in food.items():
            if nutrient.startswith("nf_") and isinstance(value, (int, float)):
                total_nutrients[nutrient] = total_nutrients.get(nutrient, 0) + value

    return total_nutrients

