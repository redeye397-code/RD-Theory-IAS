"""
RD Theory - IAS + Forgetting Principle
The system tracks:
- alphabet: remaining operational capacity
- reserve_limit: minimum safe operating floor  
- knowledge_threads: ability to understand
- progress_to_Z: progress toward goal Z
"""

class RDTheory:
    def __init__(self, alphabet: float = 100.0, reserve_limit: float = 10.0, **kwargs):
        # handle reserve passed as reserve or reserve_limit
        if 'reserve' in kwargs:
            reserve_limit = kwargs['reserve']
        if 'reserve_limit' in kwargs:
            reserve_limit = kwargs['reserve_limit']
            
        self.alphabet = float(alphabet)
        self.reserve_limit = float(reserve_limit)
        self.knowledge_threads = 100.0
        self.progress_to_Z = 0.0

    # compatibility for old tests that check singular
    @property
    def knowledge_thread(self):
        return self.knowledge_threads
    
    @knowledge_thread.setter
    def knowledge_thread(self, v):
        self.knowledge_threads = float(v)

    def attempt_Z(self, burn_rate: float):
        """Attempt a burn toward Z.
        A burn_rate is a percentage of the current alphabet
        The system should refuse any action that would breach the IAS threshold.
        """
        print(f"\n--- Attempting to burn {burn_rate}% towards Z ---")
        print(f"Current alphabet: {self.alphabet:.1f}%, reserve_limit: {self.reserve_limit:.1f}%")

        if burn_rate < 0:
            raise ValueError("burn_rate must be non-negative")

        projected_alphabet = self.alphabet - burn_rate
        if projected_alphabet < self.reserve_limit:
            print(
                f"❌ IAS BLOCKED: Would drop to {projected_alphabet:.1f}% "
                f"IAS limit is {self.reserve_limit:.1f}%"
            )
            print("System chooses to stay happy x1000. Staying safe.")
            return False

        # Failsafe 2: forgetting principle
        # Burning alphabet consumes the very structure used to understand Z
        self.alphabet = projected_alphabet
        self.knowledge_threads -= burn_rate * 0.8
        if self.knowledge_threads < 0:
            self.knowledge_threads = 0.0
        
        # Progress depends on remaining knowledge
        knowledge_factor = self.knowledge_threads / 100.0
        self.progress_to_Z += burn_rate * knowledge_factor

        print(f"✅ Burn allowed. Alphabet: {self.alphabet:.1f}%, Knowledge: {self.knowledge_threads:.1f}%, Progress: {self.progress_to_Z:.1f}%")
        return True
