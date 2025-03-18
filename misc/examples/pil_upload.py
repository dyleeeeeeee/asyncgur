#!/usr/bin/env python3
"""
Example script demonstrating how to upload a PIL-generated image to Imgur.

This example creates a random image using NumPy and PIL, then uploads it to
Imgur using the asyncgur library.
"""
import os
import sys
import logging
import asyncio
from io import BytesIO
from typing import Tuple

import numpy as np
from PIL import Image
from dotenv import load_dotenv

# Add parent directory to path to import asyncgur
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from asyncgur import Imgur, ImageInfo, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get Imgur client ID from environment variable
CLIENT_ID = os.getenv('IMGUR_CLIENT_ID')
if not CLIENT_ID:
    logger.error("IMGUR_CLIENT_ID environment variable not set")
    sys.exit(1)


async def generate_random_image(width: int = 100, height: int = 100) -> bytes:
    """Generate a random image using NumPy and PIL.
    
    Args:
        width: Width of the image in pixels
        height: Height of the image in pixels
        
    Returns:
        Image data as bytes
    """
    # Generate random RGB values
    imarray = np.random.rand(height, width, 3) * 255
    
    # Create PIL image from NumPy array
    im = Image.fromarray(imarray.astype('uint8')).convert('RGBA')
    
    # Save image to BytesIO object
    image_bytes = BytesIO()
    im.save(image_bytes, 'PNG')
    
    # Return image bytes
    return image_bytes.getvalue()


async def upload_image_to_imgur(image_data: bytes) -> Tuple[ImageInfo, Response]:
    """Upload an image to Imgur.
    
    Args:
        image_data: Image data as bytes
        
    Returns:
        Tuple containing image info and API response
    """
    async with Imgur(CLIENT_ID) as imgur_app:
        logger.info("Uploading image to Imgur...")
        image, response = await imgur_app.upload_image(
            image=image_data,
            title="Random Generated Image",
            description="This image was generated using NumPy and PIL"
        )
        logger.info(f"Image uploaded successfully! URL: {image.link}")
        return image, response


async def main():
    """Main function to run the example."""
    try:
        # Generate random image
        logger.info("Generating random image...")
        image_data = await generate_random_image(width=200, height=200)
        
        # Upload image to Imgur
        image, response = await upload_image_to_imgur(image_data)
        
        # Print image URL
        print(f"\nImage uploaded successfully!")
        print(f"Image URL: {image.link}")
        print(f"Delete hash: {image.deletehash}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Use the new asyncio API
    asyncio.run(main())