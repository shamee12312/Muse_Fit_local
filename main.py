import os
import logging
import uuid
from flask import render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import traceback

# Load environment variables from .env file if it exists (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, that's okay for Replit deployment
    pass

from app import app
from gemini import generate_tryon_image, analyze_fit_recommendation, generate_tryon_from_description, generate_enhanced_tryon

# Configure allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_uploaded_image(file, upload_type):
    """Process and save uploaded image"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        flash(f'Invalid file type for {upload_type}. Please upload PNG, JPG, JPEG, GIF, or WEBP files.')
        return None
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{upload_type}_{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        # Save and convert to JPEG for consistency
        file.save(filepath)
        
        # Convert to JPEG if needed
        if not filepath.lower().endswith('.jpg') and not filepath.lower().endswith('.jpeg'):
            try:
                with Image.open(filepath) as img:
                    # Convert to RGB if necessary (for PNG with transparency)
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    jpeg_filepath = filepath.rsplit('.', 1)[0] + '.jpg'
                    img.save(jpeg_filepath, 'JPEG', quality=90)
                    
                    # Remove original non-JPEG file
                    os.remove(filepath)
                    filepath = jpeg_filepath
            except Exception as e:
                logging.error(f"Error converting image to JPEG: {e}")
                flash(f'Error processing image. Please make sure you uploaded a valid image file.')
                return None
        
        return filepath
    except Exception as e:
        logging.error(f"Error processing image {upload_type}: {e}")
        flash(f'Error processing {upload_type} image. Please try again.')
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with upload form and try-on generation"""
    if request.method == 'POST':
        try:
            # Validate form data
            if 'user_photo' not in request.files or 'product_photo' not in request.files:
                flash('Please upload both user photo and product photo.')
                return redirect(request.url)
            
            user_file = request.files['user_photo']
            product_file = request.files['product_photo']
            
            # Process uploaded images
            user_image_path = process_uploaded_image(user_file, 'user')
            product_image_path = process_uploaded_image(product_file, 'product')
            
            if not user_image_path or not product_image_path:
                return redirect(request.url)
            
            # Extract body measurements
            try:
                body_measurements = {
                    'chest': float(request.form.get('chest', 0)),
                    'waist': float(request.form.get('waist', 0)),
                    'height': float(request.form.get('height', 0))
                }
            except (ValueError, TypeError):
                flash('Please enter valid numeric values for body measurements.')
                return redirect(request.url)
            
            # Extract product size information
            product_size = {
                'size': request.form.get('product_size', ''),
                'chest': request.form.get('product_chest', ''),
                'length': request.form.get('product_length', '')
            }
            
            # Validate required fields
            if not all([body_measurements['chest'], body_measurements['waist'], body_measurements['height']]):
                flash('Please fill in all body measurements.')
                return redirect(request.url)
            
            if not product_size['size']:
                flash('Please enter the product size.')
                return redirect(request.url)
            
            # Generate try-on visualization
            logging.info("Starting try-on generation...")
            try:
                result_image_path, recommendation = generate_tryon_image(
                    user_image_path, 
                    product_image_path, 
                    body_measurements, 
                    product_size
                )
                
                # Generate fit recommendation
                fit_recommendation = analyze_fit_recommendation(body_measurements, product_size)
                
                # Clean up uploaded files
                try:
                    os.remove(user_image_path)
                    os.remove(product_image_path)
                except OSError:
                    pass  # Files might already be deleted
                
                return render_template('index.html', 
                                     success=True,
                                     result_image=result_image_path,
                                     recommendation=recommendation,
                                     fit_recommendation=fit_recommendation,
                                     body_measurements=body_measurements,
                                     product_size=product_size)
                
            except Exception as e:
                logging.error(f"Try-on generation failed: {e}")
                logging.error(traceback.format_exc())
                flash(f'Failed to generate try-on visualization: {str(e)}')
                return redirect(request.url)
                
        except Exception as e:
            logging.error(f"Form processing error: {e}")
            logging.error(traceback.format_exc())
            flash('An error occurred while processing your request. Please try again.')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/generate-prompt', methods=['POST'])
def generate_prompt():
    """Generate try-on from text descriptions"""
    try:
        # Get descriptions from form
        user_description = request.form.get('user_description', '').strip()
        product_description = request.form.get('product_description', '').strip()
        
        if not user_description or not product_description:
            flash('Please provide both person and clothing descriptions.')
            return redirect(url_for('index'))
        
        # Generate try-on from descriptions
        logging.info("Starting prompt-based try-on generation...")
        try:
            result_image_path, recommendation = generate_tryon_from_description(
                user_description, 
                product_description
            )
            
            # Create a simple fit analysis from the descriptions
            fit_recommendation = f"Based on your description, this should look great! The AI has created a visualization showing how the {product_description.lower()} would look on {user_description.lower()}."
            
            return render_template('index.html', 
                                 success=True,
                                 result_image=result_image_path,
                                 recommendation=recommendation,
                                 fit_recommendation=fit_recommendation,
                                 user_description=user_description,
                                 product_description=product_description,
                                 prompt_generated=True)
            
        except Exception as e:
            logging.error(f"Prompt-based try-on generation failed: {e}")
            logging.error(traceback.format_exc())
            flash(f'Failed to generate try-on from description: {str(e)}')
            return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Prompt form processing error: {e}")
        logging.error(traceback.format_exc())
        flash('An error occurred while processing your request. Please try again.')
        return redirect(url_for('index'))

@app.route('/generate-enhanced', methods=['POST'])
def generate_enhanced():
    """Generate enhanced try-on with uploaded images and detailed prompts"""
    try:
        # Get uploaded files first
        if 'user_photo' not in request.files or 'product_photo' not in request.files:
            flash('Please upload both user photo and product photo first.')
            return redirect(url_for('index'))
        
        user_file = request.files['user_photo']
        product_file = request.files['product_photo']
        
        # Process uploaded images
        user_image_path = process_uploaded_image(user_file, 'user')
        product_image_path = process_uploaded_image(product_file, 'product')
        
        if not user_image_path or not product_image_path:
            return redirect(url_for('index'))
        
        # Get prompt descriptions
        person_measurements = request.form.get('person_measurements', '').strip()
        product_details = request.form.get('product_details', '').strip()
        
        if not person_measurements or not product_details:
            flash('Please provide both person measurements and product details.')
            return redirect(url_for('index'))
        
        # Generate enhanced try-on
        logging.info("Starting enhanced try-on generation...")
        try:
            result_image_path, recommendation = generate_enhanced_tryon(
                user_image_path, 
                product_image_path,
                person_measurements,
                product_details
            )
            
            # Create fit recommendation from the provided measurements
            fit_recommendation = f"Based on your measurements and the product details provided, the AI has created a personalized try-on showing how this item would fit you."
            
            # Clean up uploaded files
            try:
                os.remove(user_image_path)
                os.remove(product_image_path)
            except OSError:
                pass  # Files might already be deleted
            
            return render_template('index.html', 
                                 success=True,
                                 result_image=result_image_path,
                                 recommendation=recommendation,
                                 fit_recommendation=fit_recommendation,
                                 person_measurements=person_measurements,
                                 product_details=product_details,
                                 enhanced_generated=True)
            
        except Exception as e:
            logging.error(f"Enhanced try-on generation failed: {e}")
            logging.error(traceback.format_exc())
            flash(f'Failed to generate enhanced try-on: {str(e)}')
            return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Enhanced form processing error: {e}")
        logging.error(traceback.format_exc())
        flash('An error occurred while processing your request. Please try again.')
        return redirect(url_for('index'))

@app.route('/test-images')
def test_images():
    """Provide test images for users who don't have their own"""
    return render_template('test_images.html')

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File is too large. Please upload files smaller than 16MB.')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logging.error(f"Internal server error: {error}")
    flash('An internal error occurred. Please try again.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
