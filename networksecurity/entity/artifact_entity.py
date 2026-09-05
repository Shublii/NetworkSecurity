from dataclasses import dataclass

@dataclass
class DataIngestionArtifact:
    training_file_path: str
    test_file_path: str
    