
import torch
from torch import Tensor
import numpy as np

from typing import Union, List, Callable, Literal
from jaxtyping import Int

from src.utils import sample_without_replacement
from src.dataset.tokenizer import BalanParenTokenizer, Tokenizer, BaseTenAdditionTokenizer
from src.dataset.utils import get_addend_from_subtraction

class TokenGenerator():

    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer
    
    def gen_random_tokens(self, batch_size: int) -> Int[Tensor, 'batch pos']:
        numeric_tokens = torch.randint(0, self.tokenizer.d_vocab_numeric, (batch_size, self.tokenizer.n_ctx_numeric))
        return self.tokenizer.pad_numeric_tokens(numeric_tokens)
    
    def construct_off_by_k_tokens_generator(self, 
                                          token_generator: Callable[[int], Int[Tensor, 'batch pos']],
                                          k: int = 1
                                          ) -> Callable[[int], Int[Tensor, 'batch pos']]:
        """Construct a token generator that samples from the same distribution as the given token generator
        but with k tokens replaced by random tokens"""
        def off_by_k_tokens_generator(batch_size: int) -> Int[Tensor, 'batch pos']:
            tokens = token_generator(batch_size)
            numeric_tokens = self.tokenizer.unpad_tokens(tokens)
            replacement_tokens = torch.randint(0, self.tokenizer.d_vocab_numeric, (batch_size, k))
            replacement_idx = sample_without_replacement(self.tokenizer.n_ctx_numeric, size=(batch_size, k))
            numeric_tokens.scatter_(dim=1, index=replacement_idx, src=replacement_tokens)
            return self.tokenizer.pad_numeric_tokens(numeric_tokens)
        
        return off_by_k_tokens_generator
    
    def construct_altered_start_generator(self, 
                                          token_generator: Callable[[int], Int[Tensor, 'batch pos']],
                                          start_tokens: Int[Tensor, 'pos_start']
                                          ) -> Callable[[int], Int[Tensor, 'batch pos']]:
        def altered_start_generator(batch_size: int) -> Int[Tensor, 'batch pos']:
            tokens = token_generator(batch_size)
            numeric_tokens = self.tokenizer.unpad_tokens(tokens)
            numeric_tokens[:, :len(start_tokens)] = start_tokens
            return self.tokenizer.pad_numeric_tokens(numeric_tokens)
    
        return altered_start_generator


class BaseTenAdditionTokenGenerator(TokenGenerator):
    """Contains token generators that create the addends for the addition task.
    
    The adddends are written in reverse order, with the least significant digit first.
    """

    def __init__(self, tokenizer: BaseTenAdditionTokenizer):
        self.tokenizer = tokenizer
    
    def gen_carry_tokens(self, batch_size: int, carry_depth: int) -> Int[Tensor, 'batch pos']:
        assert 0 <= carry_depth <= self.tokenizer.n_digits_addend - 1
        max_starting_carry_pos = self.tokenizer.n_digits_addend - carry_depth
        starting_carry_pos = torch.randint(0, max_starting_carry_pos, (batch_size,))

        base_addend = self.gen_base_addend_for_carry(starting_carry_pos)
        sum_result = self.gen_sum_for_carry(base_addend, carry_depth)        
        other_addend = get_addend_from_subtraction(base_addend, sum_result, self.tokenizer)
        tokens = self.tokenizer.pad_addends_as_tokens(base_addend, other_addend)
        return tokens
    
    def gen_base_addend_for_carry(
            self,
            starting_carry_pos: Int[Tensor, 'batch'],
        ) -> Int[Tensor, 'batch digits']:
        """Generate a batch of addend tokens such that the digit at starting_carry_pos is not zero."""
        batch_size = starting_carry_pos.shape[0]
        addend = self.gen_random_sum_element_tokens(batch_size, 'addend')
        is_zero_at_starting_carry_pos = addend[:, starting_carry_pos] == 0
        non_zero_replacement = torch.randint(1, 10, (batch_size,))
        addend[:, starting_carry_pos] = torch.where(is_zero_at_starting_carry_pos,
                                                    non_zero_replacement,
                                                    addend[:, starting_carry_pos])
        return addend
    
    def gen_sum_for_carry(
            self,
            addend: Int[Tensor, 'batch digits'],
            starting_carry_pos: Int[Tensor, 'batch'],
            carry_depth: int
        ) -> Int[Tensor, 'batch digits']:
        """Generate a batch of sum tokens such that addend + (sum - addend) involves a carry_depth 
        consecutive chained carries beginning at starting_carry_pos. 
        
        For that the sum must:
        * Be lower than the addend at the position starting the chained carry
        * Be zero at the positions corresponding to the chained carry (as many as carry_depth)
        * Have a 1 at the most significant digit if the carry ends at that position
        """
        batch_size = addend.shape[0]
        sum_result = self.gen_random_sum_element_tokens(batch_size, 'sum')
        
        max_sum_at_starting_carry_pos = addend[:, starting_carry_pos]
        sum_at_starting_carry_pos = np.random.randint(0, max_sum_at_starting_carry_pos, (batch_size,))
        sum_result[:, starting_carry_pos] = sum_at_starting_carry_pos

        for shift_pos in range(1, carry_depth + 1):
            sum_result[:, starting_carry_pos + shift_pos] = 0
        
        carry_end_at_last_digit = starting_carry_pos + 1 == self.tokenizer.n_digits_addend
        sum_result[carry_end_at_last_digit, -1] = 1
        return sum_result
    
    def gen_random_sum_element_tokens(
            self,
            batch_size: int,
            sum_element: Literal['addend', 'sum']
        ) -> Int[Tensor, 'batch digits']:
        n_digits = self.tokenizer.get_num_digits_sum_element(sum_element)
        element_tokens = torch.randint(0, self.tokenizer.d_vocab_numeric, (batch_size, n_digits))
        return element_tokens


class BalanParenTokenGenerator(TokenGenerator):
    def __init__(self, tokenizer: BalanParenTokenizer):
        self.tokenizer = tokenizer

    def gen_same_num_open_and_closed_tokens(self, batch_size: int) -> Int[Tensor, 'batch pos']:
        same_num_open_and_closed_seq = self._gen_single_same_num_open_and_closed_seq()
        idx_pos_permutations = sample_without_replacement(high=self.tokenizer.n_ctx_numeric, 
                                                          size=(batch_size, self.tokenizer.n_ctx_numeric))
        numeric_tokens = same_num_open_and_closed_seq[idx_pos_permutations]
        return self.tokenizer.pad_numeric_tokens(numeric_tokens)

    def _gen_single_same_num_open_and_closed_seq(self) -> Int[Tensor, 'n_ctx_numeric']:
        half_seq_open_tokens = self.tokenizer.OPEN * torch.ones(self.tokenizer.n_ctx_numeric // 2, dtype=torch.long)
        half_seq_closed_tokens = self.tokenizer.CLOSED * torch.ones(self.tokenizer.n_ctx_numeric // 2, dtype=torch.long)
        seq = torch.cat([half_seq_open_tokens, half_seq_closed_tokens])
        return seq       
        
    def gen_balanced_parentheses_tokens(self, batch_size: int) -> Int[Tensor, 'batch pos']:
        numeric_tokens = torch.stack([self._gen_single_balanced_parenthesis_seq() for _ in range(batch_size)])
        return self.tokenizer.pad_numeric_tokens(numeric_tokens)
        
    def _gen_single_balanced_parenthesis_seq(self) -> Int[Tensor, 'n_ctx_numeric']:
        """Create a single balanced parenthesis sequence of length n_ctx_numeric.
         
        It uses an injective map between sequences with equal number of open and closed parentheses 
        and balanced sequences."""
        seq = [self.tokenizer.OPEN, self.tokenizer.CLOSED] * (self.tokenizer.n_ctx_numeric // 2) # Use list instead of tensor as we'll rely heavily on appending
        np.random.shuffle(seq)
        
        start_of_seq = []
        end_of_seq = []
        chunk = []
        count_paren = {self.tokenizer.OPEN: 0, self.tokenizer.CLOSED: 0}
        for paren in seq:
            chunk.append(paren)
            count_paren[paren] += 1
            
            if count_paren[self.tokenizer.OPEN] == count_paren[self.tokenizer.CLOSED]:
                if paren == self.tokenizer.CLOSED: # The chunk is balanced
                    start_of_seq += chunk 
                else:
                    start_of_seq.append(self.tokenizer.OPEN)
                    reverse_chunk = [1-p for p in chunk[1:-1]] # Exclude first and last parentheses and invert the rest
                    end_of_seq = [self.tokenizer.CLOSED] + reverse_chunk + end_of_seq
                chunk = [] # Reset chunk

        return torch.tensor(start_of_seq + end_of_seq)
