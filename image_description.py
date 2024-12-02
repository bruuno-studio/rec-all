from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
import torch

class ImageDescriptionGenerator:
    def __init__(self):
        self.model = None
        self.processor = None
        
    def generate_description(self, image_path):
        try:
            if self.model is None:
                model_name = "microsoft/git-base-textcaps"
                self.processor = AutoProcessor.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            with Image.open(image_path) as img:
                # Resize for efficiency
                img.thumbnail((800, 800))
                inputs = self.processor(images=img, return_tensors="pt")
                
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_length=30,
                    num_beams=1
                )
                
            return self.processor.decode(output[0], skip_special_tokens=True)
            
        except Exception as e:
            print(f"Description generation error: {e}")
            return "Image description could not be generated."