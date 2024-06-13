### Overview ###

Caldron is an AI-assisted recipe development platform that allows users to generate and quickly iterate on new recipes. 
Caldron leverages multi-agent generative artificial intelligence tools to generate a desired foundational recipe from a provided prompt and optionally provided context. Caldron then provides channels for both human and machine sensory feedback to iteratively refine the recipe.

The system works as follows:
- 1. User provides a prompt and optionally context (i.e. custom ingredients, dietary restrictions, recipe sources, etc.)
- 2. The system (Caldron) parses the request and determines what type of SQL query to execute on a local database of recipes, ingredients, and processes
- 3. Caldron executes the query and returns a list of relevant information
- 4. Caldron formats the returned information into a context for recipe generation
- 5. Caldron generates a foundational recipe based on the context and prompt.
- 6. Caldron provides the foundational recipe to the user for feedback
- 7. The user provides feedback on the recipe and the foundational recipe is tweaked until the user is satisfied
- 8. Caldron provides interaction points for human feedback (in the form of written and spoken language) and machine feedback (in the form of sensory data provided by IoT devices)
- 9. The user is free to cook/bake the recipe and provide feedback on the final product
- 10. Caldron intelligently uses this feedback to further refine the recipe as well as save a "snapshot" of the recipe attempt for future reference