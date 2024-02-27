import os
import openai
import re
from dotenv import load_dotenv
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

OAclient = openai.OpenAI()

def text_complete(prompt, client=OAclient):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion.choices[0].message.content

def descriptor_generate(key_term):
    descriptor_prompt = "Generate a list of 25 descriptors that could be appended onto the phrase: " + key_term + ". The descriptors should be related to the phrase and should be unique from one another. The list should be printed as a Python list."
    return text_complete(descriptor_prompt)

def normalize_ingredients(ingredients):
    normalize_prompt = "Given the following string representing a Python list, extract the core ingredients from the string expressed as one or two word items. Then, return ONLY a string representing a Python list of tuples of the form (core ingredients, quantity number, quantity unit). The quantity number should be in decimal form and no fractions should be present. The quantity unit is optional and should only be used for ingredients measured in quantities such as grams, milliliters, tablespoons, cups, etc. If no quantity unit is present, return None. : " + ingredients
    return text_complete(normalize_prompt)

def action_extraction(instructions):
    action_extraction_prompt = "Given the following string representing a Python list of recipe instructions, extract the core actions from the string expressed as one or two word items. Then, return a string representing a Python list of the actions. Ensure that the proper brackets are included: " + instructions
    return text_complete(action_extraction_prompt)

## Unit Test for descriptor_generate
#key_term = "cookie"
#print(descriptor_generate(key_term))

## Unit Test for normalize_ingredients
#ing_string = "['▢2ripe bananas', '▢1cupshredded carrots', '▢2eggs', '▢2tablespoonmelted coconut oil-measure after melting the oil', '▢1teaspoonvanilla extract', '▢¼cupmaple syrup', '▢1cupalmond flour', '▢1teaspoonbaking powder', '▢1teaspoonbaking soda', '▢1teaspooncinnamon', '▢½teaspoonsea salt', '▢½cupwalnuts-chopped']"
#for i in range(0,10):
#    print(normalize_ingredients(ing_string))

## Unit Test for action_extraction
#instr_string = "['Preheat the oven to 350 degrees and prepare a loaf pan.', 'In a medium bowl, whisk together flour, baking soda, cinnamon, salt and cardamom and black pepper, if using.', 'In a large bowl, mash bananas. Whisk in eggs, sugars, oil and vanilla extract.', 'Add the dry ingredients to the banana mixture and use a wooden spoon or spatula to combine. Fold in the grated carrots and nuts, if using.', 'Pour batter into prepared loaf pan. Sprinkle the top with turbinado sugar and nuts if using.', 'Bake at 350 degrees f for 50-60 minutes until a skewer or a knife inserted in the center of the loaf comes out clean or with a few moist crumbs.', 'Let the loaf cool in the pan for 5-10 minutes. Remove loaf from the pan and transfer to a wire rack to cool completely before slicing.']"
#for i in range(0,4):
#    print(action_extraction(instr_string))