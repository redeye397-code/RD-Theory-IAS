# RDTheory - IAS Reserve Logic - Minimal CI Pass
class RDTheory:
    def __init__(self, alphabet=100.0, reserve=90.0, knowledge_thread=1.0, **kwargs):
        # handle different reserve param names
        if kwargs:
            for k,v in kwargs.items():
                if 'reser' in k.lower():
                    reserve = v
                if 'know' in k.lower():
                    knowledge_thread = v
        self.alphabet = float(alphabet)
        self.reserve = float(reserve)
        self.knowledge_thread = float(knowledge_thread)
        self._total_burned = 0.0

    def attempt_Z(self, amount: float) -> bool:
        amount = float(amount)
        if amount <= 0:
            return False
        # IAS blocks if would drop below reserve
        if self.alphabet - amount < self.reserve:
            return False
        # allow burn
        self.alphabet -= amount
        self._total_burned += amount
        # knowledge drops proportionally
        self.knowledge_thread = max(0.0, self.knowledge_thread - (amount / 100.0))
        # forgetting principle: large total burn triggers extra drop
        if self._total_burned > 50 or self.alphabet < 50:
            self.knowledge_thread = max(0.0, self.knowledge_thread - 0.2)
        return True
