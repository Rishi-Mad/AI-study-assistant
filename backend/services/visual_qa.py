import cv2
import numpy as np
import pytesseract
import re
import base64
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Optional, Tuple
import io
from transformers import pipeline, BlipProcessor, BlipForQuestionAnswering
import torch
import sympy as sp
from sympy.parsing.latex import parse_latex
import requests

class VisualQAService:
    """Visual Question Answering service for math and science problems"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self.vqa_processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
            self.vqa_model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base").to(self.device)
        except Exception as e:
            print(f"Warning: Could not load VQA model: {e}")
            self.vqa_processor = None
            self.vqa_model = None
        
        # Math expression patterns
        self.math_patterns = {
            'equation': r'[a-zA-Z0-9\s]*[=][a-zA-Z0-9\s\+\-\*\/\^\.]*',
            'fraction': r'\d+\/\d+',
            'polynomial': r'[a-zA-Z]\^?\d*[\+\-]\d*[a-zA-Z]?\^?\d*',
            'integral': r'∫.*d[a-zA-Z]',
            'derivative': r'd[a-zA-Z]\/d[a-zA-Z]',
            'limit': r'lim.*→.*',
            'summation': r'∑.*=.*',
            'square_root': r'√\d+',
            'exponent': r'\d+\^\d+',
            'logarithm': r'log\d*\(.*\)|ln\(.*\)'
        }
        
        # Subject-specific keywords
        self.subject_keywords = {
            'math': [
                'solve', 'calculate', 'find', 'equation', 'derivative', 'integral', 
                'limit', 'function', 'graph', 'slope', 'area', 'volume', 'angle',
                'triangle', 'circle', 'polynomial', 'matrix', 'vector'
            ],
            'physics': [
                'force', 'velocity', 'acceleration', 'momentum', 'energy', 'power',
                'electric', 'magnetic', 'wave', 'frequency', 'amplitude', 'circuit',
                'voltage', 'current', 'resistance', 'mass', 'weight', 'gravity'
            ],
            'chemistry': [
                'molecule', 'atom', 'bond', 'reaction', 'equation', 'balance',
                'molar', 'concentration', 'solution', 'acid', 'base', 'pH',
                'electron', 'proton', 'neutron', 'orbital', 'periodic'
            ]
        }
    
    def process_image_question(self, image_file, question: str, subject: str = "general") -> Dict:
        """Main method to process image and question"""
        try:
            # Convert uploaded file to PIL Image
            image = Image.open(image_file.stream)
            
            # Enhance image quality for better OCR
            enhanced_image = self._enhance_image_for_ocr(image)
            
            # Extract text from image
            extracted_text = self._extract_text_from_image(enhanced_image)
            
            # Detect mathematical expressions
            math_expressions = self._detect_math_expressions(extracted_text)
            
            # Process based on subject
            if subject in ['math', 'physics', 'chemistry']:
                result = self._process_stem_question(
                    image, enhanced_image, question, extracted_text, math_expressions, subject
                )
            else:
                result = self._process_general_question(image, question, extracted_text)
            
            result.update({
                "extracted_text": extracted_text[:500],
                "detected_expressions": math_expressions[:5],
                "subject": subject,
                "processing_info": {
                    "ocr_confidence": self._calculate_ocr_confidence(extracted_text),
                    "math_detected": len(math_expressions) > 0,
                    "image_quality": self._assess_image_quality(enhanced_image)
                }
            })
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to process image: {str(e)}",
                "confidence": 0.0,
                "answer": "Unable to process the image. Please ensure it's clear and try again."
            }
    
    def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        if image.mode != 'L':
            image = image.convert('L')
        
        width, height = image.size
        if width < 800 or height < 600:
            scale_factor = max(800/width, 600/height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        image = image.filter(ImageFilter.UnsharpMask())
        
        return image
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text using OCR with multiple configurations"""
        text_results = []
        
        # Standard OCR configuration
        try:
            config1 = '--oem 3 --psm 6'
            text1 = pytesseract.image_to_string(image, config=config1)
            text_results.append(text1)
        except:
            pass
        
        # Math-optimized OCR configuration
        try:
            config2 = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789+-*/=()[]{}abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,√∫∑∂∞≤≥≠±'
            text2 = pytesseract.image_to_string(image, config=config2)
            text_results.append(text2)
        except:
            pass
        
        # Single block OCR
        try:
            config3 = '--oem 3 --psm 7'
            text3 = pytesseract.image_to_string(image, config=config3)
            text_results.append(text3)
        except:
            pass
        
        # Choose best result (longest non-empty text)
        best_text = max(text_results, key=len, default="")
        return best_text.strip()
    
    def _detect_math_expressions(self, text: str) -> List[Dict]:
        """Detect mathematical expressions in text"""
        expressions = []
        
        for expr_type, pattern in self.math_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                expressions.append({
                    "type": expr_type,
                    "expression": match.group().strip(),
                    "position": match.span(),
                    "confidence": self._calculate_expression_confidence(match.group(), expr_type)
                })
        
        # Sort by confidence
        expressions.sort(key=lambda x: x["confidence"], reverse=True)
        return expressions
    
    def _process_stem_question(self, image: Image.Image, enhanced_image: Image.Image, 
                              question: str, extracted_text: str, math_expressions: List[Dict], 
                              subject: str) -> Dict:
        """Process STEM (Science, Technology, Engineering, Math) questions"""
        
        # Try to solve mathematically if possible
        if subject == 'math' and math_expressions:
            math_solution = self._attempt_math_solution(math_expressions, question)
            if math_solution:
                return {
                    "answer": math_solution["solution"],
                    "confidence": math_solution["confidence"],
                    "method": "mathematical_solver",
                    "steps": math_solution.get("steps", []),
                    "expression_used": math_solution.get("expression", "")
                }
        
        # Try visual question answering if model is available
        if self.vqa_model and self.vqa_processor:
            vqa_answer = self._get_vqa_answer(image, question)
            if vqa_answer["confidence"] > 0.5:
                return vqa_answer
        
        # Fall back to rule-based analysis
        return self._rule_based_stem_analysis(question, extracted_text, math_expressions, subject)
    
    def _process_general_question(self, image: Image.Image, question: str, extracted_text: str) -> Dict:
        """Process general questions about images"""
        
        # Try VQA model first
        if self.vqa_model and self.vqa_processor:
            vqa_answer = self._get_vqa_answer(image, question)
            if vqa_answer["confidence"] > 0.3:
                return vqa_answer
        
        # Fall back to text-based analysis
        return self._text_based_analysis(question, extracted_text)
    
    def _attempt_math_solution(self, math_expressions: List[Dict], question: str) -> Optional[Dict]:
        """Attempt to solve mathematical expressions"""
        if not math_expressions:
            return None
        
        try:
            # Get the highest confidence expression
            best_expr = math_expressions[0]
            expr_text = best_expr["expression"]
            
            # Clean and prepare expression for SymPy
            cleaned_expr = self._clean_math_expression(expr_text)
            
            if best_expr["type"] == "equation":
                return self._solve_equation(cleaned_expr, question)
            elif best_expr["type"] == "derivative":
                return self._solve_derivative(cleaned_expr)
            elif best_expr["type"] == "integral":
                return self._solve_integral(cleaned_expr)
            elif best_expr["type"] in ["polynomial", "fraction"]:
                return self._evaluate_expression(cleaned_expr)
            
        except Exception as e:
            print(f"Math solving error: {e}")
            return None
    
    def _solve_equation(self, equation: str, question: str) -> Dict:
        """Solve algebraic equations"""
        try:
            # Parse equation
            if '=' in equation:
                left, right = equation.split('=', 1)
                expr = f"Eq({left.strip()}, {right.strip()})"
            else:
                expr = equation
            
            # Determine variable to solve for
            variables = re.findall(r'[a-zA-Z]', equation)
            if not variables:
                return {"solution": "No variables found to solve for", "confidence": 0.2}
            
            var = max(set(variables), key=variables.count)  # Most common variable
            
            # Solve using SymPy
            x = sp.Symbol(var)
            eq = sp.sympify(expr.replace(var, 'x'))
            solutions = sp.solve(eq, x)
            
            if solutions:
                if len(solutions) == 1:
                    solution_text = f"{var} = {solutions[0]}"
                else:
                    solution_text = f"{var} = {', '.join(map(str, solutions))}"
                
                return {
                    "solution": solution_text,
                    "confidence": 0.8,
                    "steps": [
                        f"Given equation: {equation}",
                        f"Solving for {var}:",
                        f"Solution: {solution_text}"
                    ],
                    "expression": equation
                }
            else:
                return {"solution": "No solution found", "confidence": 0.3}
                
        except Exception as e:
            return {"solution": f"Could not solve equation: {str(e)}", "confidence": 0.1}
    
    def _solve_derivative(self, expression: str) -> Dict:
        """Solve derivative problems"""
        try:
            # Extract function and variable
            match = re.search(r'd([^/]+)/d([a-zA-Z])', expression)
            if not match:
                return {"solution": "Could not parse derivative", "confidence": 0.2}
            
            func_str = match.group(1).strip()
            var = match.group(2)
            
            x = sp.Symbol(var)
            func = sp.sympify(func_str.replace(var, 'x'))
            derivative = sp.diff(func, x)
            
            return {
                "solution": f"d/d{var}[{func_str}] = {derivative}",
                "confidence": 0.8,
                "steps": [
                    f"Find the derivative of {func_str} with respect to {var}",
                    f"Result: {derivative}"
                ],
                "expression": expression
            }
            
        except Exception as e:
            return {"solution": f"Could not solve derivative: {str(e)}", "confidence": 0.1}
    
    def _solve_integral(self, expression: str) -> Dict:
        """Solve integral problems"""
        try:
            # Basic integral parsing (this would need more sophisticated parsing in practice)
            integrand_match = re.search(r'∫([^d]+)d([a-zA-Z])', expression)
            if not integrand_match:
                return {"solution": "Could not parse integral", "confidence": 0.2}
            
            integrand = integrand_match.group(1).strip()
            var = integrand_match.group(2)
            
            x = sp.Symbol(var)
            func = sp.sympify(integrand.replace(var, 'x'))
            integral = sp.integrate(func, x)
            
            return {
                "solution": f"∫{integrand}d{var} = {integral} + C",
                "confidence": 0.8,
                "steps": [
                    f"Find the integral of {integrand} with respect to {var}",
                    f"Result: {integral} + C"
                ],
                "expression": expression
            }
            
        except Exception as e:
            return {"solution": f"Could not solve integral: {str(e)}", "confidence": 0.1}
    
    def _evaluate_expression(self, expression: str) -> Dict:
        """Evaluate mathematical expressions"""
        try:
            # Clean and evaluate
            result = sp.sympify(expression)
            simplified = sp.simplify(result)
            
            return {
                "solution": f"{expression} = {simplified}",
                "confidence": 0.7,
                "steps": [
                    f"Evaluate: {expression}",
                    f"Result: {simplified}"
                ],
                "expression": expression
            }
            
        except Exception as e:
            return {"solution": f"Could not evaluate expression: {str(e)}", "confidence": 0.1}
    
    def _clean_math_expression(self, expression: str) -> str:
        """Clean mathematical expression for parsing"""
        # Replace common OCR mistakes
        replacements = {
            '×': '*',
            '÷': '/',
            '−': '-',
            '±': '+-',  # This needs special handling
            '²': '**2',
            '³': '**3',
        }
        
        cleaned = expression
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
        
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _get_vqa_answer(self, image: Image.Image, question: str) -> Dict:
        """Get answer using visual question answering model"""
        try:
            inputs = self.vqa_processor(image, question, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                outputs = self.vqa_model.generate(**inputs, max_length=50)
            
            answer = self.vqa_processor.decode(outputs[0], skip_special_tokens=True)
            
            # Calculate confidence based on answer length and content
            confidence = min(0.9, len(answer.split()) / 10 + 0.3)
            
            return {
                "answer": answer,
                "confidence": confidence,
                "method": "visual_qa_model"
            }
            
        except Exception as e:
            print(f"VQA model error: {e}")
            return {"answer": "", "confidence": 0.0}
    
    def _rule_based_stem_analysis(self, question: str, extracted_text: str, 
                                 math_expressions: List[Dict], subject: str) -> Dict:
        """Rule-based analysis for STEM questions"""
        
        # Analyze question intent
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['solve', 'find', 'calculate', 'what is']):
            if math_expressions:
                # Try to provide guidance on solving
                expr = math_expressions[0]
                guidance = self._get_solving_guidance(expr, subject)
                return {
                    "answer": guidance,
                    "confidence": 0.6,
                    "method": "rule_based_guidance",
                    "detected_expression": expr["expression"]
                }
        
        # Default response with extracted information
        response = f"I can see this text in the image: {extracted_text[:200]}..."
        if math_expressions:
            response += f"\n\nMathematical expressions detected: {', '.join([e['expression'] for e in math_expressions[:3]])}"
        
        return {
            "answer": response,
            "confidence": 0.4,
            "method": "text_extraction"
        }
    
    def _text_based_analysis(self, question: str, extracted_text: str) -> Dict:
        """Analyze question based on extracted text"""
        if not extracted_text.strip():
            return {
                "answer": "I couldn't extract clear text from this image. Please ensure the image is clear and well-lit.",
                "confidence": 0.1
            }
        
        # Simple keyword matching
        question_words = set(question.lower().split())
        text_words = set(extracted_text.lower().split())
        
        overlap = len(question_words.intersection(text_words))
        
        if overlap > 0:
            return {
                "answer": f"Based on the text I can see: {extracted_text[:300]}...",
                "confidence": min(0.7, overlap / len(question_words)),
                "method": "text_matching"
            }
        
        return {
            "answer": f"Here's what I can read from the image: {extracted_text[:300]}",
            "confidence": 0.3,
            "method": "text_extraction"
        }
    
    def _get_solving_guidance(self, expression: Dict, subject: str) -> str:
        """Provide guidance on how to solve the expression"""
        expr_type = expression["type"]
        expr_text = expression["expression"]
        
        guidance_map = {
            "equation": f"To solve the equation '{expr_text}', isolate the variable by performing the same operations on both sides.",
            "derivative": f"To find the derivative of '{expr_text}', apply the power rule, product rule, or chain rule as appropriate.",
            "integral": f"To solve the integral '{expr_text}', find the antiderivative and add the constant of integration.",
            "fraction": f"To simplify the fraction '{expr_text}', find the greatest common divisor of numerator and denominator.",
            "polynomial": f"To work with the polynomial '{expr_text}', you might need to factor, expand, or find roots depending on the question."
        }
        
        return guidance_map.get(expr_type, f"I detected a {expr_type} expression: '{expr_text}'. Please specify what you'd like to do with it.")
    
    def _calculate_expression_confidence(self, expression: str, expr_type: str) -> float:
        """Calculate confidence score for detected mathematical expressions"""
        confidence = 0.5  # Base confidence
        
        # Length factor (reasonable length expressions are more likely correct)
        if 3 <= len(expression) <= 50:
            confidence += 0.2
        
        # Contains expected characters for the type
        type_chars = {
            'equation': '=',
            'fraction': '/',
            'polynomial': '^+-',
            'integral': '∫d',
            'derivative': 'd/',
            'square_root': '√'
        }
        
        if expr_type in type_chars:
            if any(char in expression for char in type_chars[expr_type]):
                confidence += 0.2
        
        # Avoid common OCR mistakes
        if not re.search(r'[|\\]{2,}', expression):  # No multiple pipes/backslashes
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_ocr_confidence(self, text: str) -> float:
        """Calculate overall OCR confidence based on text characteristics"""
        if not text.strip():
            return 0.0
        
        confidence = 0.5
        
        # Check for reasonable word/character ratios
        words = text.split()
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            if 2 <= avg_word_length <= 12:  # Reasonable average word length
                confidence += 0.2
        
        # Check for reasonable character distribution
        alpha_ratio = sum(c.isalpha() for c in text) / len(text)
        if 0.3 <= alpha_ratio <= 0.9:  # Good mix of letters
            confidence += 0.2
        
        # Penalty for excessive special characters (OCR artifacts)
        special_ratio = sum(not c.isalnum() and not c.isspace() for c in text) / len(text)
        if special_ratio > 0.3:
            confidence -= 0.3
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_image_quality(self, image: Image.Image) -> str:
        """Assess image quality for OCR"""
        width, height = image.size
        
        # Size assessment
        if width < 400 or height < 300:
            return "low"
        elif width > 1200 and height > 800:
            return "high"
        else:
            return "medium"