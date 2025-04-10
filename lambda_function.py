import sys
sys.path.append("package")

import json
import logging
import string
from rapidfuzz import fuzz

# Set up logging with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for detailed scoring
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("/tmp/chatbot_debug.log"),
        logging.StreamHandler()
    ]
)
logging.getLogger().setLevel(logging.DEBUG)

# Global quote index for cycling through motivational quotes
quote_index = 0

# Enhanced thesaurus for synonym expansion
THESAURUS = {
    "definition": {"define", "meaning", "description", "explain", "clarify"},
    "fitness": {"health", "exercise", "wellness", "strength", "vitality"},
    "motivation": {"inspiration", "encouragement", "drive", "push", "spirit"},
    "injury": {"hurt", "pain", "damage", "strain", "trauma"},
    "workout": {"exercise", "training", "gym", "routine", "session"},
    "abs": {"abdominal", "stomach", "core", "midsection", "belly"},
    "history": {"past", "olden", "ancient", "heritage", "tradition"},
    "weight": {"mass", "pounds", "kilograms", "bodyweight", "load"},
    "steps": {"walk", "stride", "pace", "movement", "count"},
    "diet": {"nutrition", "food", "eating", "meal", "regimen"},
    "recovery": {"heal", "repair", "restore", "recuperate", "mend"},
    "prevent": {"avoid", "stop", "reduce", "protect", "guard"},
    "busy": {"occupied", "hectic", "full", "tight", "pressed"},
    "muscle": {"tissue", "strength", "fiber", "power", "bulk"},
    "exercise": {"activity", "movement", "fitness", "practice", "drill"}
}

# Q&A Dataset (unchanged except for clarity)
qa_data = [
    {
        "id": "weight_loss_struggle",
        "keywords": [
            "my weight is stuck", "struggle", "why not weight-loss", "why am not losing my weight", 
            "weight not reduced", "not reducing", "not gaining", "not gaining my weight", 
            "not balance", "no result", "no improvemment", "no improvemments", 
            "not improve", "no progress", "progress", "weight stuck", "weight plateau", 
            "not seeing results", "why is my weight stuck", "what's stopping my weight loss", 
            "why is my weight not changing", "cant lose weight", "weight loss stalled", 
            "difficulty losing", "weight issues", "stagnant weight", "why no weight change",
            "losing struggle", "plateau problem", "weight loss barrier", "no weight drop"
        ],
        "answer": (
            "Plateaus can be incredibly frustrating when the effort you put in doesn't immediately translate into visible results. "
            "Consistency is your most powerful tool. Focus on these five essential factors:\n"
            "1. Diet & Caloric Balance\n"
            "2. Metabolic Differences\n"
            "3. Hormonal & Health Issues\n"
            "4. Lifestyle Factors\n"
            "5. Proper Hydration\n"
            "Embrace the process with patience, knowing that even unseen progress is paving the way for long-term results."
        )
    },
    {
        "id": "daily_steps",
        "keywords": [
            "steps", "walk", "daily", "daily steps", "recommended steps", "walking", "run", 
            "how much should i run", "count.Concurrent.futures", "step goal", "benefits of steps", "benefits of walking", 
            "pros of walk", "why walk", "need of walking", "need of walk", "nessecitity of walk", 
            "resason for walk", "how many steps should I take daily", "is walking good for me", 
            "how much walking is enough", "step count", "daily movement", "walking routine", 
            "step target", "walking benefits", "daily pace", "how far to walk", "walking amount"
        ],
        "answer": (
            "Aiming for 7,000–8,000 steps daily boosts your cardiovascular health, strengthens muscles, and enhances mental well-being. "
            "It also aids weight management and lowers chronic disease risks. Start by tracking your current steps and gradually increase your count."
        )
    },
    {
        "id": "ancient_fitness",
        "keywords": [
            "history", "history of ancient people", "goolden era fitness", "olden fitness", 
            "old people fitness", "olden days", "what was fitness like long ago", 
            "how did ancient people stay fit", "fitness in ancient times", "exercise in the past", 
            "ancient exercise", "past fitness", "historical fitness", "olden health", 
            "ancient wellness", "fitness heritage", "traditional fitness", "past activity",
            "how ancients exercised", "old fitness methods"
        ],
        "answer": (
            "Exercise, as structured physical activity, became popular relatively recently. Ancient people stayed fit through active lifestyles—"
            "hunting, farming, and manual labor naturally kept them in shape. Their simpler diets and closer-to-nature living contributed to overall fitness."
        )
    },
    {
        "id": "exercise_frequency",
        "keywords": [
            "often", "exercise week", "how much workout", "how much gym", "how much exercise", 
            "daily gym", "cardio workout frequency", "active rest days", "rest day importance", 
            "weekly gym schedule", "optimal workout frequency", "consistent exercise", 
            "ideal duration", "workout duration", "workout time", "hours of workout", 
            "time spend in gym", "hours enough in gym", "more hours in gym", 
            "how often should I exercise", "how many days to work out", "is daily exercise okay", 
            "how long should workouts be", "exercise routine", "gym regularity", "workout consistency",
            "exercise timing", "weekly exercise plan", "daily workout okay", "rest vs exercise"
        ],
        "answer": (
            "Aim for 3–5 workout sessions per week, with each session lasting 30–60 minutes. For general health, 30 minutes of moderate exercise works well, "
            "while more intense sessions can extend to an hour. Include one or two rest days to allow for muscle recovery and injury prevention."
        )
    },
    {
        "id": "muscle_soreness",
        "keywords": [
            "sore", "muscles pain", "soreness", "muscle cramp", "muscle fatigue", "muscle tear", 
            "tissue tear", "sore-muscle", "pain", "why are my muscles sore after exercise", 
            "what causes muscle soreness", "why do I feel pain after working out", 
            "post-workout pain", "muscle ache", "exercise soreness", "stiff muscles", 
            "pain after gym", "sore after workout", "muscle discomfort", "workout stiffness"
        ],
        "answer": (
            "Muscles feel sore after exercise because the physical strain causes tiny tears in the muscle fibers. "
            "This triggers an inflammatory response during repair, leading to pain and stiffness (commonly known as delayed onset muscle soreness, or DOMS)."
        )
    },
    {
        "id": "muscle_recovery",
        "keywords": [
            "muscle recover", "muscle recovery", "muscle tissue repair", "repair", "muscle build time", 
            "muscle build", "muscles recover", "body recovery", "body repair", 
            "how to recover muscles faster", "best ways to repair muscles", "how to speed up recovery", 
            "muscle healing", "post-exercise recovery", "repair muscles", "faster recovery", 
            "muscle restoration", "recovery tips", "heal after workout", "body mend"
        ],
        "answer": (
            "- Walk or cycle lightly to boost blood flow.\n"
            "- Stretch or foam roll to ease tightness.\n"
            "- Hydrate and consume protein-rich foods.\n"
            "- Ensure ample sleep for muscle repair.\n"
            "- Use warm/cool treatments to reduce inflammation."
        )
    },
    {
        "id": "prevent_injury",
        "keywords": [
            "prevent", "injury", "workouts", "recover injury", "recover form pain", "types of injury", 
            "safely workout", "cons of bad posture", "side effects of wrong posture", 
            "side effects of wrong workout", "side effect of wrong workout", 
            "how to avoid workout injuries", "how to exercise safely", "how to prevent getting hurt", 
            "injury prevention", "safe exercise", "avoid harm", "reduce injury risk", 
            "workout safety", "protect from injury", "exercise caution"
        ],
        "answer": (
            "- Warm up and cool down.\n"
            "- Focus on proper form.\n"
            "- Progress gradually.\n"
            "- Rest when necessary.\n"
            "- Use quality equipment."
        )
    },
    {
        "id": "fit_exercise_busy",
        "keywords": [
            "busy", "busy schedule", "no time", "not enough time", "not getting time", 
            "few hours", "exhausted", "office busy", "long day", 
            "how to exercise with a busy schedule", "how to fit workouts in a busy day", 
            "what to do when I have no time", "tight schedule workout", "busy life exercise", 
            "no free time", "hectic day fitness", "quick workouts", "exercise on the go", 
            "busy routine fitness", "time crunch workout"
        ],
        "answer": (
            "Consider these tips:\n"
            "- Incorporate 15–20 minute workouts.\n"
            "- Treat exercise like a meeting.\n"
            "- Use stairs or walk during calls.\n"
            "- Start your day with a quick workout.\n"
            "- Focus on general body exercises."
        )
    },
    {
        "id": "creator_info",
        "keywords": [
            "creator", "owner", "created chatbot", "inspired by", "creation of chatbot", 
            "chatbot birthday", "personal project", "chatbot build", "when build this bot", 
            "purpose of bot", "purpose of chatbot", "unique owner", "unique thing about owner", 
            "place of owner", "when created", "date of chatbot", "name of chatbot", 
            "chatbot name", "name", "who created this chatbot", "what’s the purpose of this bot", 
            "when was this bot made", "bot origin", "chatbot maker", "bot creation date", 
            "who made this", "bot intent", "creator details", "chatbot story"
        ],
        "answer": (
            "~ Sihha Health Chatbot\n"
            "~ Created by khan Mohammed in Hyderabad, Telangana\n"
            "~ A project named Sihha, launched in April 2023\n"
            "~ Provides open-source, evidence-based fitness guidance and health support\n"
            "~ Driven by the commitment to democratize accessible and reliable health resources"
        )
    },
    {
        "id": "fitness_definition",
        "keywords": [
            "fitness", "definition", "fitness definition", "define fitness", "about fitness", 
            "what is fitness", "how do you define fitness", "what does fitness mean", 
            "fitness meaning", "explain fitness", "fitness description", "what’s fitness", 
            "fitness explained", "health definition", "wellness meaning", "fitness concept"
        ],
        "answer": (
            "Fitness is defined by the efficient, coordinated performance of your body's systems—most notably the cardiovascular, respiratory, "
            "musculoskeletal, and metabolic systems."
        )
    },
    {
        "id": "exercise_benefits",
        "keywords": [
            "exercise", "benefits", "health benefits", "pros of workout", "pros of fitness", 
            "benefits of fitness", "gym benefits", "why fitness", "why gym", "is fitness important", 
            "how does exercise help me", "why is working out good", "what are the benefits of gym", 
            "exercise advantages", "fitness perks", "workout gains", "health pros", 
            "gym advantages", "why exercise matters", "benefits of activity"
        ],
        "answer": (
            "Exercise is a strategic investment in both body and mind 💪🧠. It enhances cardiovascular health 💓, strengthens muscles 💪, "
            "and boosts mental clarity while reducing stress 😌. It also improves memory and focus through increased blood flow."
        )
    },
    {
        "id": "balanced_diet",
        "keywords": [
            "balanced diet", "diet", "what to eat", "weight loss diet", "weight gain diet", 
            "diet for maintanaine", "diet for reduce weigth", "diet for muscle building", 
            "diet for muscle loss", "pre-workout", "eat", "post-workout", "snacks", "protein", 
            "meal plan", "suggest a diet plan", "before workout", "after workout", 
            "what should I eat for balance", "best diet for muscle gain", "how to plan my meals", 
            "nutrition plan", "healthy eating", "food for fitness", "diet guide", 
            "meal balance", "eating routine", "diet suggestions"
        ],
        "answer": "For our complete guide on diet and workout plans, view our services."
    },
    {
        "id": "beginner_workout",
        "keywords": [
            "beginner workout", "workout", "best workout", "balannce workout", "weight loss workout", 
            "weight gain workout", "workout for thin", "how to start working out", 
            "best workout for beginners", "simple workout for newbies", "starter workout", 
            "newbie exercise", "easy workout", "beginner routine", "first workout", 
            "workout for starters", "basic exercise", "intro to workout"
        ],
        "answer": "For our complete guide on diet and workout plans, view our services."
    },
    {
        "id": "abs_exercises",
        "keywords": [
            "abs", "abs exercises", "abs workout", "workout for stomach", "tummy workout", 
            "lower belly workout", "lower belly", "upper belly workout", "uper belly", 
            "reduce stomach", "six packs abs workout", "six packs", "6 packs", 
            "how to get abs", "best exercises for stomach", "how to build six-pack abs", 
            "core workout", "abdominal routine", "stomach exercises", "abs training", 
            "belly fat workout", "six-pack routine", "core strength exercises"
        ],
        "answer": (
            "Exercises like Weight Plate Crunches, Seated Cable Crunches, Decline Cable Crunches, Weighted Plank, Dumbbell Side Bend, "
            "High to Low Cable Woodchop, Overhead Squats, and Dumbbell Knee Raises can help build abs. Remember, exercise alone isn’t enough to reduce stubborn stomach fat— a balanced, nutrient-rich diet is also essential."
        )
    },
    {
        "id": "strength_or_cardio",
        "keywords": [
            "today", "what to do", "which excersice to do", "what to perform", 
            "my mood to do cardio", "my mood to do muscle building", "my mood to do swimming", 
            "my mood to do cross fit", "should I do strength or cardio", "what exercise should I do today", 
            "cardio or weights", "strength vs cardio", "daily exercise choice", "cardio or lifting", 
            "what workout today", "exercise mood", "cardio vs strength", "today’s workout"
        ],
        "answer": (
            "If you're pumped, hit the weights 💪; if you're in the mood for intensity, choose cardio 🏃. You can also mix both: start with strength training, then finish with a burst of cardio for an extra kick. Let your mood guide your workout—and enjoy every moment."
        )
    },
    {
        "id": "calories_daily",
        "keywords": [
            "calories daily", "daily calories intake", "calories", "best calories intake", "best calorie", 
            "how many calories should I eat daily", "what’s my daily calorie need", "how much to eat per day", 
            "calorie count", "daily energy", "calorie needs", "food intake", "calories per day", 
            "daily calorie goal", "how many calories", "calorie requirement"
        ],
        "answer": "Your daily calorie needs depend on your BMR (basal metabolic rate) and activity level."
    },
    {
        "id": "weight_loss_pace",
        "keywords": [
            "weight-loss", "pace", "ideal", "weight to reduce", "reduce weight per week", "fast reducing weight", 
            "rapid weight loss", "fast weight loss", "quick weight loss", "soon weight loss", 
            "side effects of weight loss", "slow weight loss", "how fast should I lose weight", 
            "what’s a safe weight loss pace", "how much weight to lose weekly", "weight loss speed", 
            "safe weight drop", "weight loss rate", "ideal weight loss", "weekly weight goal"
        ],
        "answer": (
            "A safe, sustainable weight-loss goal is generally around 1 to 2 pounds (0.5 to 1 kilogram) per week. This pace helps preserve muscle mass, supports steady progress, and minimizes health risks. Individual factors like your starting weight and metabolism will influence what's ideal for you."
        )
    },
    {
        "id": "motivational_quote",
        "keywords": [
            "motivational", "fitness quote", "quote", "inspiration", "dont like going gym", 
            "gym is boring", "fitness is boring", "why weight loss", "dont like physical activity", 
            "no physical activity", "give me a fitness quote", "how to stay motivated", 
            "inspire me to exercise", "motivation boost", "fitness inspiration", "exercise drive", 
            "keep going", "stay inspired", "gym motivation", "workout push"
        ],
        "answers": [
            "You don’t have to be great to start, but you have to start to be great.",
            "Take care of your body. It’s the only place you have to live.",
            "Motivation is what gets you started. Habit is what keeps you going.",
            "A feeble body weakens the mind.",
            "If you think lifting is dangerous, try being weak. Being weak is dangerous."
        ]
    },
    {
        "id": "fitness_myths",
        "keywords": [
            "fitness myths", "exercise myths", "workout misconceptions", "training myths", 
            "exercise fads and facts", "fitness facts vs. myths", "fitness misinformation", 
            "exercise rumors", "cardio misconceptions", "workout fallacies", 
            "what are common fitness myths", "true or false about exercise", 
            "what’s a workout misconception", "fitness falsehoods", "exercise myths debunked", 
            "workout myths", "fitness rumors", "training misconceptions", "exercise facts", 
            "myth vs reality fitness"
        ],
        "answer": (
            "Fitness myths, exercise myths, and workout misconceptions can lead to training myths and unproven exercise fads. "
            "Distinguishing fitness facts vs. myths is key to countering fitness misinformation, exercise rumors, cardio misconceptions, and workout fallacies."
        )
    }
]

# Preprocess keywords with thesaurus expansion
for entry in qa_data:
    keyword_set = set()
    for keyword in entry["keywords"]:
        keyword = keyword.lower().translate(str.maketrans('', '', string.punctuation))
        words = keyword.split()
        keyword_set.update(words)
        for word in words:
            if word in THESAURUS:
                keyword_set.update(THESAURUS[word])
    entry["keyword_set"] = keyword_set

def preprocess_text(text):
    """Convert text to lowercase, remove punctuation, and split into words."""
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    return set(text.split())

def get_matching_answer(user_question):
    """Find the best matching answer with refined scoring."""
    global quote_index
    logging.info(f"User question received: {user_question}")
    user_words = preprocess_text(user_question)
    logging.debug(f"Preprocessed user words: {user_words}")
    
    best_match = None
    highest_score = 0
    
    try:
        if not user_words:
            raise ValueError("Empty preprocessed question")

        for entry in qa_data:
            # Base score from common words
            common_words = user_words.intersection(entry["keyword_set"])
            score = len(common_words) * 10
            
            # Exact match boost and fuzzy matching
            question_lower = user_question.lower()
            for keyword in entry["keywords"]:
                keyword_lower = keyword.lower()
                if keyword_lower == question_lower:
                    score += 100  # Exact match boost
                    logging.debug(f"Exact match: '{keyword}'")
                else:
                    partial_ratio = fuzz.partial_ratio(question_lower, keyword_lower)
                    token_sort_ratio = fuzz.token_sort_ratio(question_lower, keyword_lower)
                    combined_fuzzy_score = (partial_ratio + token_sort_ratio) / 2
                    if combined_fuzzy_score > 85:
                        score += int(combined_fuzzy_score / 10)
                        logging.debug(f"Fuzzy match: '{keyword}' = {combined_fuzzy_score}")
            
            logging.debug(f"Score for '{entry['id']}': {score}")
            if score > highest_score:
                highest_score = score
                best_match = entry
        
        if best_match and highest_score > 5:
            logging.info(f"Best matched entry: {best_match['id']} with score {highest_score}")
            if best_match["id"] == "motivational_quote":
                answers = best_match["answers"]
                answer = answers[quote_index]
                quote_index = (quote_index + 1) % len(answers)
                return answer
            return best_match["answer"]
        
        logging.warning("No suitable match found.")
        return ("It's not you, its me😔. We don't have a direct answer at this time; "
                "our FAQ might have the clever insight you need.")
    
    except ValueError as ve:
        logging.error(f"Value error: {str(ve)}")
        return "Sorry, I couldn’t process your question. Please try rephrasing it."
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise RuntimeError(f"Failed to process question: {str(e)}")

def lambda_handler(event, context):
    """Handle incoming Lambda event with flexible payload parsing."""
    try:
        logging.info(f"Raw event: {event}")
        if isinstance(event, dict):
            if 'body' in event:
                body = event['body']
                if isinstance(body, str):
                    data = json.loads(body)
                else:
                    data = body
            else:
                data = event
        else:
            data = json.loads(event)
        
        user_question = data.get('question', '').strip()
        if not user_question:
            logging.warning("Missing or empty question.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing or empty question'})
            }
        
        answer = get_matching_answer(user_question)
        logging.info(f"Final answer: {answer[:60]}...")
        return {
            'statusCode': 200,
            'body': json.dumps({'answer': answer})
        }
    
    except json.JSONDecodeError as json_err:
        logging.error(f"JSON parsing error: {str(json_err)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON format', 'details': str(json_err)})
        }
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)})
        }

# For local testing
if __name__ == "__main__":
    test_cases = [
        ("My weight is stuck, what should I do", "weight_loss_struggle"),
        ("How many steps should I take every day?", "daily_steps"),
        ("What's the definition of fitness?", "fitness_definition")
    ]
    for question, expected_id in test_cases:
        print(f"\nTesting: {question}")
        answer = get_matching_answer(question)
        print(f"Response: {answer}")