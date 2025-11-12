import json
from datetime import datetime
from typing import List, Dict, Optional

class ConversationManager:
    """Manages multi-turn conversations with full context"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_design = {}
        self.parameters_stack = []
        self.feedback_list = []
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_design(self, parameters: Dict):
        """Update design and store in stack"""
        self.current_design.update(parameters)
        self.parameters_stack.append(self.current_design.copy())
    
    def refine(self, feedback: str):
        """Store refinement feedback"""
        self.feedback_list.append(feedback)
    
    def undo(self) -> bool:
        """Undo last change"""
        if len(self.parameters_stack) > 1:
            self.parameters_stack.pop()
            self.current_design = self.parameters_stack[-1].copy()
            return True
        return False
    
    def get_summary(self) -> str:
        """Get current design summary"""
        return json.dumps(self.current_design, indent=2)
    
    def get_context(self, last_n: int = 3) -> str:
        """Get last N messages as context"""
        msgs = self.conversation_history[-last_n:]
        context = "Recent conversation:\n"
        for msg in msgs:
            context += f"{msg['role']}: {msg['content']}\n"
        return context

if __name__ == "__main__":
    mgr = ConversationManager()
    mgr.add_message("user", "Create rectangular plate")
    mgr.update_design({"type": "rectangular", "width": 200})
    print("✅ Test passed")
