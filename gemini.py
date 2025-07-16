import json
import logging
import os
import base64
from google import genai
from google.genai import types
from pydantic import BaseModel



client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


class TryOnResult(BaseModel):
    success: bool
    recommendation: str
    fit_description: str


def analyze_image(jpeg_image_path: str) -> str:
    """Analyze an image and return detailed description"""
    with open(jpeg_image_path, "rb") as f:
        image_bytes = f.read()
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                "Analyze this image in detail and describe its key " +
                "elements, context, and any notable aspects.",
            ],
        )

    return response.text if response.text else ""


def generate_tryon_image(user_image_path: str, product_image_path: str, 
                        body_measurements: dict, product_size: dict) -> str:
    """Generate a try-on visualization using Gemini"""
    try:
        # Read user image
        with open(user_image_path, "rb") as f:
            user_image_bytes = f.read()
        
        # Read product image  
        with open(product_image_path, "rb") as f:
            product_image_bytes = f.read()

        # Create detailed prompt for try-on generation
        prompt = f"""
        Create a realistic try-on visualization showing the person wearing the clothing item. 
        
        User measurements:
        - Chest: {body_measurements.get('chest', 'N/A')} inches
        - Waist: {body_measurements.get('waist', 'N/A')} inches  
        - Height: {body_measurements.get('height', 'N/A')} inches
        
        Product size information:
        - Size: {product_size.get('size', 'N/A')}
        - Chest: {product_size.get('chest', 'N/A')} inches
        - Length: {product_size.get('length', 'N/A')} inches
        
        Generate a photorealistic image showing the person from the first image wearing the clothing item from the second image. 
        Ensure proper fit and proportions based on the measurements provided. The result should look natural and realistic.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=[
                types.Part.from_bytes(
                    data=user_image_bytes,
                    mime_type="image/jpeg",
                ),
                types.Part.from_bytes(
                    data=product_image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )

        if not response.candidates:
            raise Exception("No response candidates generated")

        content = response.candidates[0].content
        if not content or not content.parts:
            raise Exception("No content parts in response")

        # Save the generated image
        output_path = None
        recommendation_text = "Try-on generated successfully!"
        
        for part in content.parts:
            if part.text:
                recommendation_text = part.text
                logging.info(f"Generated recommendation: {part.text}")
            elif part.inline_data and part.inline_data.data:
                output_path = "static/results/tryon_result.jpg"
                with open(output_path, 'wb') as f:
                    f.write(part.inline_data.data)
                logging.info(f"Try-on image saved as {output_path}")

        return output_path, recommendation_text

    except Exception as e:
        logging.error(f"Failed to generate try-on image: {e}")
        if "INVALID_ARGUMENT" in str(e) and "Unable to process input image" in str(e):
            raise Exception("The uploaded images couldn't be processed. Please make sure you uploaded clear, valid image files (JPEG, PNG, etc.)")
        elif "INVALID_ARGUMENT" in str(e):
            raise Exception("Invalid input provided. Please check your images and try again.")
        else:
            raise Exception(f"Failed to generate try-on visualization: {e}")


def analyze_fit_recommendation(body_measurements: dict, product_size: dict) -> str:
    """Generate fit recommendation based on measurements"""
    try:
        prompt = f"""
        Analyze the fit between user body measurements and product size information.
        
        User measurements:
        - Chest: {body_measurements.get('chest', 'N/A')} inches
        - Waist: {body_measurements.get('waist', 'N/A')} inches
        - Height: {body_measurements.get('height', 'N/A')} inches
        
        Product size:
        - Size: {product_size.get('size', 'N/A')}
        - Chest: {product_size.get('chest', 'N/A')} inches
        - Length: {product_size.get('length', 'N/A')} inches
        
        Provide a brief, helpful recommendation about the fit. Be specific about whether this size 
        would be comfortable, tight, loose, or perfect. Suggest alternatives if needed.
        Keep the response under 50 words and friendly in tone.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text if response.text else "This size should work well for you!"

    except Exception as e:
        logging.error(f"Failed to analyze fit: {e}")
        return "Unable to analyze fit at this time. Please check the measurements and try again."


def generate_tryon_from_description(user_description: str, product_description: str):
    """Generate a try-on visualization from text descriptions"""
    try:
        prompt = f"""
        Create a realistic try-on visualization based on these descriptions:
        
        Person: {user_description}
        
        Clothing Item: {product_description}
        
        Generate a photorealistic image showing the described person wearing the described clothing item. 
        The image should be high quality, well-lit, and show how the clothing fits on the person. 
        Make it look natural and realistic as if it's an actual photo of someone wearing the item.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )

        if not response.candidates:
            raise Exception("No response candidates generated")

        content = response.candidates[0].content
        if not content or not content.parts:
            raise Exception("No content parts in response")

        # Save the generated image
        output_path = None
        recommendation_text = "Try-on generated successfully from description!"
        
        for part in content.parts:
            if part.text:
                recommendation_text = part.text
                logging.info(f"Generated recommendation: {part.text}")
            elif part.inline_data and part.inline_data.data:
                output_path = "static/results/tryon_prompt_result.jpg"
                with open(output_path, 'wb') as f:
                    f.write(part.inline_data.data)
                logging.info(f"Prompt-based try-on image saved as {output_path}")

        return output_path, recommendation_text

    except Exception as e:
        logging.error(f"Failed to generate try-on from description: {e}")
        raise Exception(f"Failed to generate try-on from description: {e}")


def generate_enhanced_tryon(user_image_path: str, product_image_path: str, 
                           person_measurements: str, product_details: str):
    """Generate enhanced try-on with uploaded images and detailed prompts"""
    try:
        # Read user image
        with open(user_image_path, "rb") as f:
            user_image_bytes = f.read()
        
        # Read product image  
        with open(product_image_path, "rb") as f:
            product_image_bytes = f.read()

        # Create enhanced prompt combining images and descriptions
        prompt = f"""
        Create a realistic try-on visualization using the uploaded images and these details:
        
        Person measurements and details: {person_measurements}
        
        Product size and details: {product_details}
        
        Using the person's photo and the product photo provided, generate a photorealistic image showing 
        this person wearing the clothing item. Pay careful attention to the measurements provided to ensure 
        proper fit and proportions. The result should look natural and realistic, taking into account both 
        the visual information from the photos and the specific measurements and details provided.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=[
                types.Part.from_bytes(
                    data=user_image_bytes,
                    mime_type="image/jpeg",
                ),
                types.Part.from_bytes(
                    data=product_image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )

        if not response.candidates:
            raise Exception("No response candidates generated")

        content = response.candidates[0].content
        if not content or not content.parts:
            raise Exception("No content parts in response")

        # Save the generated image
        output_path = None
        recommendation_text = "Enhanced try-on generated successfully!"
        
        for part in content.parts:
            if part.text:
                recommendation_text = part.text
                logging.info(f"Generated enhanced recommendation: {part.text}")
            elif part.inline_data and part.inline_data.data:
                output_path = "static/results/tryon_enhanced_result.jpg"
                with open(output_path, 'wb') as f:
                    f.write(part.inline_data.data)
                logging.info(f"Enhanced try-on image saved as {output_path}")

        return output_path, recommendation_text

    except Exception as e:
        logging.error(f"Failed to generate enhanced try-on: {e}")
        if "INVALID_ARGUMENT" in str(e) and "Unable to process input image" in str(e):
            raise Exception("The uploaded images couldn't be processed. Please make sure you uploaded clear, valid image files (JPEG, PNG, etc.)")
        elif "INVALID_ARGUMENT" in str(e):
            raise Exception("Invalid input provided. Please check your images and try again.")
        else:
            raise Exception(f"Failed to generate enhanced try-on visualization: {e}")
