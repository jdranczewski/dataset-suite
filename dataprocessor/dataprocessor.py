class DataProcessor:
    def __init__(self, pipeline=None, storage=None):
        if pipeline is None:
            self.pipeline = []
        else:
            self.pipeline = pipeline
        
        if storage is None:
            self.storage = {}
        else:
            self.storage = storage
            
        if len(self.pipeline):
            self.next_processor = self.pipeline[0](self.pipeline[1:], self.storage)
        else:
            self.next_processor = None
    
    def run(self, dataset):
        self.run_next(dataset)
        
    def run_next(self, dataset):
        if self.next_processor is not None:
            self.next_processor.run(dataset)
