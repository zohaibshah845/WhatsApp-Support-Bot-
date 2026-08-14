# rag_engine.py - UPDATED VERSION (Aapki data.json ke liye)
import os
import json

class RAGEngine:
    def __init__(self, openai_api_key, chroma_path='data/chromadb'):
        self.openai_api_key = openai_api_key
        self.faq_data = []
        self.documents_text = ""
        
        # OpenAI client (optional)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=openai_api_key)
            self.use_openai = True
            print("✅ OpenAI client ready!")
        except:
            self.use_openai = False
            print("⚠️ OpenAI nahi hai, simple matching use hogi")
        
        # Documents load karo
        self.load_all_documents()
    
    def load_all_documents(self):
        """Sab documents load karo"""
        print("\n📚 Documents load ho rahe hain...")
        
        # data.json check karo (project root)
        if os.path.exists('data.json'):
            print("📄 data.json file mili!")
            self.load_json_file('data.json')
        
        # data/faqs folder check karo
        if os.path.exists('data/faqs'):
            for filename in os.listdir('data/faqs'):
                file_path = os.path.join('data/faqs', filename)
                if filename.endswith('.json'):
                    print(f"📄 JSON file mili: data/faqs/{filename}")
                    self.load_json_file(file_path)
                elif filename.endswith('.txt'):
                    print(f"📄 TXT file mili: data/faqs/{filename}")
                    text = self.load_text_file(file_path)
                    self.parse_text_faq(text)
        
        total_faqs = len(self.faq_data)
        print(f"\n✅ Total {total_faqs} Q&A pairs loaded!")
        
        if total_faqs == 0:
            print("⚠️ Koi document nahi mila!")
    
    def load_json_file(self, file_path):
        """JSON file load karo - List ya Dict format support karta hai"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Agar data list hai (aapka format)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'question' in item and 'answer' in item:
                        self.faq_data.append({
                            'question': item['question'].lower().strip(),
                            'answer': item['answer']
                        })
                print(f"✅ {len(data)} FAQs list se loaded!")
            
            # Agar data dict hai (company_info + faqs format)
            elif isinstance(data, dict):
                if 'company_info' in data:
                    self.company_info = data['company_info']
                
                if 'faqs' in data and isinstance(data['faqs'], list):
                    for faq in data['faqs']:
                        if isinstance(faq, dict) and 'question' in faq and 'answer' in faq:
                            self.faq_data.append({
                                'question': faq['question'].lower().strip(),
                                'answer': faq['answer']
                            })
                    print(f"✅ {len(data['faqs'])} FAQs dict se loaded!")
                
                # Simple key-value format
                for key, value in data.items():
                    if key not in ['company_info', 'faqs'] and isinstance(value, str):
                        self.faq_data.append({
                            'question': key.lower().strip(),
                            'answer': value
                        })
        
        except Exception as e:
            print(f"❌ JSON load error ({file_path}): {e}")
    
    def load_text_file(self, file_path):
        """TXT file load karo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ TXT error: {e}")
            return ""
    
    def parse_text_faq(self, text):
        """TXT file se Q&A parse karo"""
        lines = text.split('\n')
        current_q = None
        current_a = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Q:') or line.startswith('Question:'):
                if current_q and current_a:
                    self.faq_data.append({
                        'question': current_q.lower(),
                        'answer': ' '.join(current_a)
                    })
                current_q = line.split(':', 1)[1].strip()
                current_a = []
            elif line.startswith('A:') or line.startswith('Answer:'):
                current_a.append(line.split(':', 1)[1].strip())
            elif current_q and current_a:
                current_a.append(line)
        
        if current_q and current_a:
            self.faq_data.append({
                'question': current_q.lower(),
                'answer': ' '.join(current_a)
            })
    
    def find_best_match(self, question):
        """Simple matching se best answer dhoondo"""
        question_lower = question.lower().strip()
        
        # Greetings check karo (sab se pehle)
        greetings = {
            'hi': 'hi',
            'hello': 'hello',
            'salam': 'salam',
            'asalam': 'asalam',
            'assalam': 'assalam',
            'hey': 'hey',
            'ola': 'ola'
        }
        
        if question_lower in greetings:
            for faq in self.faq_data:
                if faq['question'] in greetings.values():
                    return faq['answer']
        
        # Exact match
        for faq in self.faq_data:
            if question_lower == faq['question']:
                return faq['answer']
        
        # Partial match - question contains FAQ question
        for faq in self.faq_data:
            if faq['question'] in question_lower:
                return faq['answer']
        
        # Keyword matching
        best_match = None
        best_score = 0
        
        stop_words = {'kya', 'hai', 'hain', 'ka', 'ki', 'ke', 'mein', 'par', 
                      'aap', 'hum', 'the', 'is', 'are', 'to', 'of', 'in', 
                      'se', 'ko', 'ne', 'bhi', 'aur', 'ya', 'karo', 'karein',
                      'how', 'what', 'when', 'where', 'which', 'who', 'why',
                      'do', 'does', 'did', 'can', 'could', 'would', 'should'}
        
        # Question se keywords extract karo
        keywords = set(word for word in question_lower.split() 
                      if word not in stop_words and len(word) > 2)
        
        for faq in self.faq_data:
            faq_question = faq['question']
            score = 0
            
            # Keyword matching
            for keyword in keywords:
                if keyword in faq_question:
                    score += 2
            
            # Word overlap
            faq_words = set(faq_question.split())
            overlap = keywords & faq_words
            score += len(overlap) * 3
            
            if score > best_score:
                best_score = score
                best_match = faq['answer']
        
        if best_score >= 2:
            return best_match
        
        return None
    
    def query(self, question):
        """Customer ke sawal ka jawab dhoondo"""
        try:
            # Pehle simple matching try karo
            simple_answer = self.find_best_match(question)
            
            if simple_answer:
                return simple_answer
            
            # Agar OpenAI available hai
            if self.use_openai and self.faq_data:
                try:
                    context = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" 
                                        for faq in self.faq_data[:20]])
                    
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": """Tum ek helpful customer support bot ho.
                            Urdu aur English mix mein jawab do.
                            Agar answer information mein milta hai to jawab do.
                            Agar answer nahi milta to exactly bolo: "Main Malik se poch ke batata hun"
                            Jawab chota aur clear rakho."""},
                            {"role": "user", "content": f"Information:\n{context}\n\nCustomer: {question}"}
                        ],
                        temperature=0.7,
                        max_tokens=200
                    )
                    
                    answer = response.choices[0].message.content.strip()
                    
                    if answer and "Main Malik se poch ke" not in answer:
                        return answer
                    
                except Exception as e:
                    print(f"OpenAI error: {e}")
            
            # Greetings ke liye special handling
            if question.lower().strip() in ['hi', 'hello', 'salam', 'hey']:
                return "Assalam o Alaikum! 😊 Malik Trading Company mein khush amdeed. Main aapki kya madad kar sakta hun?"
            
            return "Main Malik se poch ke batata hun"
            
        except Exception as e:
            print(f"Query error: {e}")
            return "Main Malik se poch ke batata hun"
    
    def add_document(self, file_path):
        """Naya document add karo"""
        try:
            print(f"\n📄 Document add ho raha hai: {file_path}")
            
            if file_path.endswith('.json'):
                self.load_json_file(file_path)
            elif file_path.endswith('.txt'):
                text = self.load_text_file(file_path)
                if text:
                    self.parse_text_faq(text)
            else:
                return False, "Sirf JSON aur TXT files supported hain"
            
            return True, f"Document add ho gaya! Ab {len(self.faq_data)} Q&A pairs hain."
        except Exception as e:
            return False, f"Error: {str(e)}"


# Test function
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 RAG Engine Test")
    print("=" * 50)
    
    rag = RAGEngine("test-key")
    
    test_questions = [
        "hi",
        "hello",
        "Company ka naam kya hai",
        "Delivery kitne din mein hogi",
        "Payment methods",
        "Return policy kya hai",
        "Contact number"
    ]
    
    print("\n📝 Test Results:")
    print("-" * 50)
    
    for q in test_questions:
        print(f"\n👤: {q}")
        answer = rag.query(q)
        print(f"🤖: {answer}")
    
    print("\n" + "=" * 50)
    print("✅ Test Complete!")
    print("=" * 50)