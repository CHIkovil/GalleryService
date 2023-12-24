from transformers import PreTrainedModel, PreTrainedTokenizerFast

class TransformersSetup:
    def __init__(self, *,
                 model: PreTrainedModel,
                 tokenizer: PreTrainedTokenizerFast,
                 processor):
        self.model = model
        self.tokenizer = tokenizer
        self.processor = processor
