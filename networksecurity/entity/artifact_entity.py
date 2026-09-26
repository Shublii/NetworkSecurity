# Why it is important

# Keeps the output of every pipeline step.

# Creates a separate folder for each run using a timestamp.

# Prevents old results from being overwritten.

# Makes debugging and testing easier.

# Allows the saved model to be reused for prediction.




from dataclasses import dataclass

@dataclass
class DataIngestionArtifact:
    training_file_path: str
    test_file_path: str


@dataclass
class DataValidationArtifact:
    validation_status: bool
    valid_train_file_path: str
    valid_test_file_path: str
    invalid_train_file_path: str
    invalid_test_file_path: str
    drift_report_file_path: str  


@dataclass
class DataTransformationArtifact:
    transformed_object_file_path: str
    transformed_train_file_path: str
    transformed_test_file_path: str
    
      